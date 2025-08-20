

import pytest
from ai_powered_jenkins_auditor.models.pipeline import Pipeline

def test_example_1_parser_ignores_scripted_pipeline(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("example_1_scripted_pipeline")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert isinstance(pipeline, Pipeline)
    assert len(pipeline.stages) == 0
    assert pipeline.agent is None

def test_example_2_extracts_environment_variable(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("example_2_environment_variable")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert pipeline.agent == "any"
    assert isinstance(pipeline.environment, dict)
    assert pipeline.environment.get("BUILD_MODE") == "'release'"

def test_example_3_extracts_secret_environment_variable(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("example_3_secret_environment_variable")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert pipeline.agent == "any"
    assert pipeline.environment.get("AWS_SECRET_KEY") == "'AKIA1234567890XYZ'"
    assert any("$AWS_SECRET_KEY" in step for step in pipeline.stages[0].steps)


def test_example_5_valid_multibranch_pipeline(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("example_5_multibranch_pipeline")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert pipeline.agent == "any"
    assert pipeline.environment.get("DEPLOY_ENV") == "'staging'"
    assert len(pipeline.stages) == 3
    assert any("withCredentials" in step for step in pipeline.stages[2].steps)

def test_parser_correctly_parses_block_agent(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("block_agent")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert isinstance(pipeline.agent, str)
    assert "label 'ubuntu-22.04'" in pipeline.agent

def test_parser_handles_no_agent_defined(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("no_agent_defined")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert pipeline.agent is None

def test_parser_extracts_complex_post_block(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("complex_post_block")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert "always" in pipeline.post
    assert "success" in pipeline.post
    assert "failure" in pipeline.post

def test_parser_handles_parallel_stages(parser, load_jenkinsfile):
    jenkinsfile_content = load_jenkinsfile("parallel_stages")
    pipeline = parser.parse(bytes(jenkinsfile_content, "utf-8"))
    assert len(pipeline.stages) > 0

def test_parser_handles_empty_and_invalid_files_gracefully(parser, load_jenkinsfile):
    pipeline_empty = parser.parse(bytes(load_jenkinsfile("empty"), "utf-8"))
    assert isinstance(pipeline_empty, Pipeline)
    assert len(pipeline_empty.stages) == 0

    pipeline_comments = parser.parse(bytes(load_jenkinsfile("comments_only"), "utf-8"))
    assert isinstance(pipeline_comments, Pipeline)
    assert len(pipeline_comments.stages) == 0

    pipeline_malformed = parser.parse(bytes(load_jenkinsfile("malformed"), "utf-8"))
    assert isinstance(pipeline_malformed, Pipeline)