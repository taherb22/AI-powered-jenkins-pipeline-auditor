from __future__ import annotations
from tree_sitter import Parser, Language, Node
from tree_sitter_groovy import language as get_groovy_pointer
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage       



class JenkinsFileParser:
    """
    Parses a Jenkinsfile and orchestrates linters to find issues.

    This parser relies on the `tree-sitter-groovy` grammar. The general structure
    of the AST for a declarative Jenkinsfile is a series of nested 'method_invocation'
    nodes. Understanding this structure is key to writing the data extraction logic.

    Here is a conceptual, simplified representation of the AST:

    program
    └── method_invocation (The `pipeline { ... }` block)
        ├── identifier (text: "pipeline")
        └── closure (The `{ ... }` block containing the pipeline's content)
            ├── expression_statement
            │   └── method_invocation (e.g., the `agent` block)  <-- A Top-Level Section
            │       ├── identifier (text: "agent")
            │       ├── identifier (text: "any")  # For: agent any
            │       └── closure                     # For: agent { ... }
            │           └── juxt_function_call        # For: agent { label '...' }
            │               ├── identifier (text: "label")
            │               └── argument_list
            │                   └── string_literal (text: "'my-agent'")
            │
            ├── expression_statement
            │   └── method_invocation (The `stages` block)     <-- A Top-Level Section
            │       ├── identifier (text: "stages")
            │       └── closure
            │           └── method_invocation (A `stage` block)
            │               ├── identifier (text: "stage")
            │               ├── argument_list (The stage name)
            │               │   └── string_literal (text: "'Build'")
            │               └── closure (The stage's content)
            │                   └── method_invocation (The `steps` block)
            │                       ├── identifier (text: "steps")
            │                       └── closure
            │                           └── method_invocation (A step like `sh '...'`)
            │                               ├── identifier (text: "sh")
            │                               └── argument_list / closure
            │                                   └── string_literal (text: "'echo "hello"'")
            │
            └── expression_statement
                └── method_invocation (The `environment` block) <-- A Top-Level Section
                    ├── identifier (text: "environment")
                    └── closure
                        └── assignment_expression (e.g., a line like `KEY = 'value'`)
                            ├── identifier (text: "KEY")
                            ├── operator (text: "=")
                            └── string_literal (text: "'value'")

    The core takeaway is that almost every declarative section (`pipeline`, `agent`,
    `stages`, `stage`, `steps`, `sh`, `post`, `when`, etc.) is parsed as a
    'method_invocation' node. the  task is to find these nodes and then
    inspect their children to extract the relevant data.
    """

   
    METHOD_NODE_TYPE = 'method_invocation'

    def __init__(self):
        groovy_pointer = get_groovy_pointer()
        groovy_language = Language(groovy_pointer)
        self.parser = Parser()
        self.parser.language = groovy_language

    def parse(self, text: bytes) -> Pipeline:
        tree = self.parser.parse(text)
        pipeline = Pipeline()
        
        
        pipeline_nodes = self._find_method_invocations(tree.root_node, 'pipeline')

        if pipeline_nodes:
            self._parse_pipeline_block(pipeline_nodes[0], pipeline)
        else:
            print("Warning: No 'pipeline' block was found in the parsed file.")
            
        return pipeline

    def _parse_pipeline_block(self, node: Node, pipeline: Pipeline) -> None:
        block = self._find_block(node)
        if block:
            # The children of the pipeline block are the main sections
            for child in block.named_children:
                self._dispatch(child, pipeline)

    

    def _dispatch(self, node: Node, pipeline: Pipeline) -> None:
        # The node might be wrapped in an expression_statement
        node_to_check = node
        if node.type == 'expression_statement' and node.named_child_count > 0:
            node_to_check = node.named_children[0]

        
        # Use the new helper to get the name, regardless of node type
        name = self._get_block_name(node_to_check)
        
        if name == 'agent':
            pipeline.agent = self._parse_agent(node_to_check)
        elif name == 'stages':
            pipeline.stages = self._parse_stages(node_to_check)
        elif name == 'environment':
            pipeline.environment = self._parse_environment(node_to_check)
        elif name == 'post':
            pipeline.post = self._parse_post(node_to_check)


    
    def _get_directive_name(self, node: Node) -> str | None:
        """
        A robust helper to get the name of any Jenkinsfile directive,
        whether it's a method_invocation or a local_variable_declaration.
        """
        # Case 1: For blocks like `stages { ... }`
        if node.type == self.METHOD_NODE_TYPE:
            return self._get_method_name(node)
        
        # Case 2: For directives like `agent any`
        if node.type == 'local_variable_declaration':
            # The structure is (type_identifier 'agent', variable_declarator 'any')
            # The name of the directive is the type_identifier.
            if node.child_count > 0 and node.children[0].type == 'type_identifier':
                return node.children[0].text.decode('utf8')
                
        return None
    
    def _find_method_invocations(self, node: Node, method_name: str) -> list[Node]:
        """
        Finds all descendant nodes that are method invocations with a specific name.
        """
        nodes_to_visit = [node]
        found_nodes = []
        while nodes_to_visit:
            current_node = nodes_to_visit.pop(0)
            if current_node.type == self.METHOD_NODE_TYPE and self._get_method_name(current_node) == method_name:
                found_nodes.append(current_node)
            nodes_to_visit.extend(current_node.children)
        return found_nodes
    

    

    def _get_block_name(self, node: Node) -> str | None:
        """
        A robust helper to get the name of any Jenkinsfile directive,
        whether it's a method_invocation or a local_variable_declaration.
        """
        # Case 1: For blocks like `stages { ... }`
        if node.type == self.METHOD_NODE_TYPE:
            # We can reuse your existing helper for this
            return self._get_method_name(node)
        
        # Case 2: For directives like `agent any`
        if node.type == 'local_variable_declaration':
            if node.child_count > 0 and node.children[0].type == 'type_identifier':
                return node.children[0].text.decode('utf8')
                
        return None
    
    def _get_method_name(self, node: Node) -> str | None:
        # In a method_invocation, the name is the first child if it's an identifier
        if node.child_count > 0 and node.children[0].type == 'identifier':
            return node.children[0].text.decode()
        return None

    def _find_block(self, node: Node) -> Node | None:
        # The block is usually the last child of a method_invocation
        if node.child_count > 0 and node.children[-1].type == 'closure':
            return node.children[-1]
        return None

    def _find_direct_children(self, node: Node, typ: str) -> list[Node]:
        return [c for c in node.children if c.type == typ]

    def _simple_arg(self, node: Node) -> str | None:
        # Find the argument_list node
        for child in node.children:
            if child.type == 'argument_list' and child.named_child_count > 0:
                # Return the text of the first argument, stripping quotes
                return child.named_children[0].text.decode().strip("'\"")
        return None

    

    def _parse_agent(self, node: Node) -> any:
        """
        Parses an 'agent' directive, which can be a method_invocation
        (for blocks) or a local_variable_declaration (for simple types).
        """
        # Case 1: Handles 'agent any', 'agent none'
        if node.type == 'local_variable_declaration':
            # Structure: (type_identifier 'agent', variable_declarator 'any')
            # The value we want is the text of the second child.
            if node.child_count > 1:
                return node.children[1].text.decode('utf8')

        # Case 2: Handles block agents like 'agent { docker { ... } }'
        if node.type == self.METHOD_NODE_TYPE:
            # First, check for a simple argument like { label 'my-node' }
            simple_arg = self._simple_arg(node)
            if simple_arg:
                return simple_arg
            
            # If no simple arg, parse the block
            block = self._find_block(node)
            if block:
                # This is where your complex block parsing logic for docker/kubernetes goes.
                # Returning the inner text is a robust fallback.
                return block.text.decode('utf8').strip('{}').strip()

        # Fallback if the structure is unrecognized
        return None

        
    

    def _parse_environment(self, env_node: Node) -> dict[str, str]:
        """
        Parses an environment block and extracts all key-value pairs.
        """
        key_values = {}
        
        # First, find the { ... } block
        block = self._find_block(env_node)
        if not block:
            return key_values
        
        # Based on the syntax tree, each KEY = 'value' is an 'assignment_expression'
        # often wrapped in an 'expression_statement'.
        for child in block.children:
            # The node we want might be directly a child, or wrapped.
            assign_node = child
            if child.type == 'expression_statement' and child.child_count > 0:
                assign_node = child.children[0]
                
            if assign_node.type == 'assignment_expression' and assign_node.child_count >= 3:
                # The structure is (key, '=', value)
                key_node = assign_node.children[0]
                value_node = assign_node.children[2]
                
                # Extract the raw text. The test expects the value to include its quotes.
                key = key_node.text.decode('utf8')
                value = value_node.text.decode('utf8')
                
                key_values[key] = value
                
        return key_values

    def _parse_stages(self, node: Node) -> list[Stage]:
        stages = []
        block = self._find_block(node)
        if block:
            # Find all the 'stage' invocations inside the 'stages' block
            stage_invocations = self._find_method_invocations(block, 'stage')
            for inv in stage_invocations:
                stages.append(self._parse_stage(inv))
        return stages

    def _parse_stage(self, node: Node) -> Stage:
        name = self._simple_arg(node) or 'unknown'
        stage = Stage(name)
        block = self._find_block(node)
        if block:
            # Find and parse the 'when' directive if it exists
            when_invocations = self._find_method_invocations(block, 'when')
            if when_invocations:
                stage.when = self._parse_when(when_invocations[0])

            # Find and parse the 'steps' directive
            steps_invocations = self._find_method_invocations(block, 'steps')
            if steps_invocations:
                steps_block = self._find_block(steps_invocations[0])
                if steps_block:
                    for step_node in steps_block.named_children:
                        stage.steps.append(step_node.text.decode().strip())
            
            # Find and parse the 'post' directive if it exists
            post_invocations = self._find_method_invocations(block, 'post')
            if post_invocations:
                stage.post = self._parse_post(post_invocations[0])
        return stage
    


        # In the JenkinsFileParser class...

        # In the JenkinsFileParser class...

    def _parse_when(self, node: Node) -> list[str]:
        """
        Parses the 'when' block by extracting the text of all meaningful
        statements inside its closure.
        """
        conditions = []
        block = self._find_block(node) # This finds the closure node
        if block:
            # The children of the closure are the conditions, often wrapped
            # in 'expression_statement'. We get the text of all named children.
            for child in block.named_children:
                conditions.append(child.text.decode().strip())
        return conditions
    
    def _parse_post(self, node: Node) -> dict[str, list[str]]:
        post_actions = {}
        block = self._find_block(node)
        if block:
            for child in block.named_children:
                condition_inv = child
                # Handle the expression_statement wrapper
                if condition_inv.type == 'expression_statement' and condition_inv.named_child_count > 0:
                    condition_inv = condition_inv.named_children[0]
                
                if condition_inv.type == self.METHOD_NODE_TYPE:
                    condition_name = self._get_method_name(condition_inv)
                    if condition_name:
                        actions = []
                        steps_block = self._find_block(condition_inv)
                        if steps_block:
                            for step_node in steps_block.named_children:
                                actions.append(step_node.text.decode().strip())
                        post_actions[condition_name] = actions
        return post_actions

    

