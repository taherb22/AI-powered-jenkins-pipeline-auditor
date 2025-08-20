from __future__ import annotations
import logging
from tree_sitter import Parser, Language, Node
from tree_sitter_groovy import language as get_groovy_pointer
from ai_powered_jenkins_auditor.models.pipeline import Pipeline
from ai_powered_jenkins_auditor.models.stage import Stage
from ai_powered_jenkins_auditor.jenkins_files_parser.config import *
import inspect
logger = logging.getLogger(__name__)


def unwrap_block(func):
    """Decorator to automatically extract the closure block from a node."""
    def wrapper(self, node: Node, *args, **kwargs):
        block = self._find_block(node)
        if not block:
            if "dict" in func.__annotations__.get('return', ''): return {}
            if "list" in func.__annotations__.get('return', ''): return []
            return None
        return func(self, block, *args, **kwargs)
    return wrapper

class JenkinsFileParser:
    def __init__(self):
        """Initializes the parser and loads the Groovy language grammar."""
        groovy_pointer = GROOVY_LANGUAGE_POINTER or get_groovy_pointer()
        groovy_language = Language(groovy_pointer)
        self.parser = Parser()
        self.parser.language = groovy_language
        self.pipeline: Pipeline | None = None

        # Node type constants
        self.METHOD_NODE_TYPE = METHOD_NODE_TYPE
        self.EXPRESSION_STATEMENT_NODE = EXPRESSION_STATEMENT_NODE
        self.DEFAULT_STAGE_NAME = DEFAULT_STAGE_NAME

    # ------------------ Public Interface ------------------ #
    def parse(self, text: bytes) -> Pipeline:
        """Parse Jenkinsfile content into a structured Pipeline object."""
        self.pipeline = Pipeline()
        try:
            tree = self.parser.parse(text)
            pipeline_nodes = self._find_method_invocations(tree.root_node, 'pipeline')
            if not pipeline_nodes:
                logger.warning("No 'pipeline' block found.")
                return self.pipeline
            self._parse_pipeline_block(pipeline_nodes[0])
        except Exception as e:
            logger.error(f"Failed to parse Jenkinsfile: {e}", exc_info=True)
        return self.pipeline

    # ------------------ Pipeline Parsing ------------------ #
    def _parse_pipeline_block(self, node: Node) -> None:
        """Parse top-level pipeline block directives."""
        block = self._find_block(node)
        if not block:
            logger.warning("No block found in pipeline node.")
            return
        for child in block.named_children:
            self._dispatch(child)

    # ------------------ Node Dispatch ------------------ #
    def _dispatch(self, node: Node) -> None:
        """Route a directive node to its specific parsing function."""
        node_to_check = node
        if node.type == self.EXPRESSION_STATEMENT_NODE and node.named_child_count > 0:
            node_to_check = node.named_children[0]

        name = self._get_block_name(node_to_check)
        if not name:
            logger.debug("No block name found; skipping dispatch.")
            return

        parser_map = {
            AGENT_DIRECTIVE: self._parse_agent,
            'stages': self._parse_stages,
            ENVIRONMENT_DIRECTIVE: self._parse_environment,
            POST_DIRECTIVE: self._parse_post,
        }

        parser_method = parser_map.get(name)
        if not parser_method:
            logger.debug(f"No parser method for block: {name}")
            return

        parsed_data = parser_method(node_to_check)
        if inspect.isgenerator(parsed_data):
            parsed_data = list(parsed_data)
        if hasattr(self.pipeline, name):
            setattr(self.pipeline, name, parsed_data)

    # ------------------ Helpers ------------------ #
    def _text(self, node: Node) -> str:
        """Decode and strip text from a node."""
        try:
            return node.text.decode().strip()
        except Exception:
            return ""

    def _find_block(self, node: Node) -> Node | None:
        """Return the closure block for a node."""
        if node.child_count == 0:
            return None
        last_child = node.children[-1]
        return last_child if last_child.type == CLOSURE else None

    def _find_method_invocations(self, node: Node, method_name: str) -> list[Node]:
        """Recursively find all 'method_invocation' nodes with a specific name."""
        found_nodes = []
        nodes_to_visit = [node]
        while nodes_to_visit:
            current = nodes_to_visit.pop()
            if current.type == self.METHOD_NODE_TYPE and self._get_method_name(current) == method_name:
                found_nodes.append(current)
            nodes_to_visit.extend(current.children)
        return found_nodes

    def _get_method_name(self, node: Node) -> str | None:
        if node.child_count > 0 and node.children[0].type == IDENTIFIER:
            return node.children[0].text.decode()
        return None

    def _get_block_name(self, node: Node) -> str | None:
        if node.type == self.METHOD_NODE_TYPE:
            return self._get_method_name(node)
        if node.type == LOCAL_VAR_DECLARATION and node.child_count > 0:
            if node.children[0].type == TYPE_IDENTIFIER:
                return node.children[0].text.decode('utf8')
        return None

    def _simple_arg(self, node: Node) -> str | None:
        """Extract first simple string argument from a method invocation."""
        for child in node.children:
            if child.type == ARGUMENT_LIST and child.named_child_count > 0:
                return child.named_children[0].text.decode().strip(STRING_ARG_QUOTES)
        return None

    # ------------------ Directive Parsers ------------------ #
    def _parse_agent(self, node: Node) -> str | None:
        """Parse agent directive."""
        try:
            if node.type == METHOD_NODE_TYPE:
                block = self._find_block(node)
                if block:
                    return "".join(self._text(c) for c in block.children).strip('{}').strip()
            elif node.type == LOCAL_VAR_DECLARATION:
                if node.named_child_count > 0:
                    return node.named_children[-1].text.decode('utf8')
            return None
        except Exception as e:
            logger.error(f"Failed to parse agent: {e}", exc_info=True)
            return None


    @unwrap_block
    def _parse_environment(self, block: Node) -> dict[str, str]:
        env = {}
        for child in block.children:
            assign_node = child
            if child.type == EXPRESSION_STATEMENT_NODE and child.child_count > 0:
                assign_node = child.children[0]
            if assign_node.type == ASSIGNMENT_EXPRESSION and assign_node.child_count >= 3:
                key = assign_node.children[0].text.decode('utf8')
                value = assign_node.children[2].text.decode('utf8')
                env[key] = value
        return env

    def _parse_stages(self, stages_node: Node) -> list[Stage]:
        """
        Robustly parse 'stages' by finding all 'stage' method_invocation nodes
        inside the stages closure and parsing them in source-order.
        """
        stages: list[Stage] = []

        # find the closure for the stages node (unwrap common wrappers)
        block = self._find_block(stages_node)
        if block is None and stages_node.type == self.EXPRESSION_STATEMENT_NODE and stages_node.named_child_count > 0:
            # unwrap expression_statement -> method_invocation(...) { ... }
            stages_node = stages_node.named_children[0]
            block = self._find_block(stages_node)

        if not block:
            return stages

        # find all 'stage' invocations under the stages block
        stage_nodes = self._find_method_invocations(block, 'stage')
        # preserve textual/source order
        stage_nodes.sort(key=lambda n: getattr(n, "start_byte", 0))

        for sn in stage_nodes:
            stages.append(self._parse_stage(sn))

        return stages


    def _parse_stage(self, stage_node: Node) -> Stage:
        """Parse a single stage with nested directives (steps, when, etc.)."""
        stage_name = self._simple_arg(stage_node) or self.DEFAULT_STAGE_NAME
        stage = Stage(stage_name)

      
        block = self._find_block(stage_node)
        if not block:
            # try unwrap if stage_node was wrapped inside expression_statement
            if stage_node.type == self.EXPRESSION_STATEMENT_NODE and stage_node.named_child_count > 0:
                stage_node = stage_node.named_children[0]
                block = self._find_block(stage_node)
            if not block:
                return stage

        
        steps_nodes = self._find_method_invocations(block, STEPS_DIRECTIVE)
        if steps_nodes:
           
            steps_nodes.sort(key=lambda n: getattr(n, "start_byte", 0))
            steps_block = self._find_block(steps_nodes[0])
            if steps_block:
                stage.steps = self._parse_steps_block(steps_block)

      
        when_nodes = self._find_method_invocations(block, WHEN_DIRECTIVE)
        if when_nodes:
            when_nodes.sort(key=lambda n: getattr(n, "start_byte", 0))
            when_block = self._find_block(when_nodes[0])
            if when_block:
                stage.when = [self._text(n) for n in when_block.named_children]

        return stage


    def _parse_steps_block(self, steps_block: Node) -> list[str]:
        """Return a list of textual steps found inside a steps { ... } closure."""
        steps: list[str] = []
        for child in steps_block.named_children:
            steps.extend(self._extract_step(child))
        return steps


    def _extract_step(self, node: Node) -> list[str]:
        """
        Recursively extract step strings from a node. Handles:
        - expression_statement -> unwrap
        - method_invocation -> name + arg or nested block
        - juxt_function_call -> multiple function calls like `sh 'x'`
        - fallback -> raw text
        """
        result: list[str] = []

        
        if node.type == self.EXPRESSION_STATEMENT_NODE and node.named_child_count > 0:
            return self._extract_step(node.named_children[0])

      
        if node.type == self.METHOD_NODE_TYPE:
            method_name = self._get_method_name(node) or "<unknown>"
            args = self._simple_arg(node)
            block_node = self._find_block(node)
            if block_node:
                nested = self._parse_steps_block(block_node)
                nested_text = "\n".join(nested)
                result.append(f"{method_name} {{\n{nested_text}\n}}")
            elif args:
              
                result.append(f"{method_name} '{args}'")
            else:
                result.append(method_name)
            return result

        if node.type == "juxt_function_call" or node.type == "function_call_expression":
            for c in node.named_children:
                result.extend(self._extract_step(c))
            return result

        if node.named_child_count > 0:
            for c in node.named_children:
                result.extend(self._extract_step(c))
            return result

      
        text = self._text(node).strip()
        if text:
            result.append(text)
        return result


    @unwrap_block
    def _parse_post(self, block: Node) -> dict[str, list[str]]:
        post_actions = {}
        for cond_node in block.children:
            if cond_node.type == EXPRESSION_STATEMENT_NODE and cond_node.named_child_count > 0:
                cond_node = cond_node.named_children[0]
            if cond_node.type == METHOD_NODE_TYPE:
                name = self._get_method_name(cond_node)
                if name:
                    steps_block = self._find_block(cond_node)
                    post_actions[name] = [self._text(n) for n in steps_block.named_children] \
                        if steps_block else []
        return post_actions
