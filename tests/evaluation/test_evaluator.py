"""Tests for the evaluation framework."""

from __future__ import annotations

from planos.app.evaluation.datasets import (
    get_all_eval_cases,
    get_analyst_agent_cases,
    get_finance_agent_cases,
    get_planning_agent_cases,
)
from planos.app.evaluation.evaluator import Evaluator
from planos.app.evaluation.models import EvalCase, EvalReport


class TestEvalDatasets:
    """Test evaluation datasets."""

    def test_planning_cases_not_empty(self):
        cases = get_planning_agent_cases()
        assert len(cases) > 0
        assert all(isinstance(c, EvalCase) for c in cases)

    def test_finance_cases_not_empty(self):
        cases = get_finance_agent_cases()
        assert len(cases) > 0

    def test_analyst_cases_not_empty(self):
        cases = get_analyst_agent_cases()
        assert len(cases) > 0

    def test_all_cases_have_required_fields(self):
        cases = get_all_eval_cases()
        for case in cases:
            assert case.id
            assert case.name
            assert case.input
            assert len(case.expected_tools) > 0

    def test_case_ids_are_unique(self):
        cases = get_all_eval_cases()
        ids = [c.id for c in cases]
        assert len(ids) == len(set(ids))


class TestEvaluator:
    """Test evaluator functionality."""

    def test_evaluate_case_success(self):
        evaluator = Evaluator(agent_name="test", model="mock")
        case = EvalCase(
            id="test-001",
            name="Test",
            description="Test case",
            input="Create a scenario",
            expected_tools=["create_scenario"],
            expected_output_properties={"scenario_id"},
        )

        def mock_agent(input_text: str) -> dict:
            return {
                "tools_used": ["create_scenario"],
                "output": {"scenario_id": "test-id", "status": "created"},
                "tokens_used": 100,
            }

        result = evaluator.evaluate_case(case, mock_agent)
        assert result.success is True
        assert result.tools_correct is True
        assert result.output_valid is True

    def test_evaluate_case_wrong_tool(self):
        evaluator = Evaluator(agent_name="test", model="mock")
        case = EvalCase(
            id="test-002",
            name="Wrong tool",
            description="Wrong tool",
            input="Create",
            expected_tools=["create_scenario"],
        )

        def mock_agent(input_text: str) -> dict:
            return {"tools_used": ["delete_scenario"], "output": {}, "tokens_used": 50}

        result = evaluator.evaluate_case(case, mock_agent)
        assert result.success is False
        assert result.tools_correct is False

    def test_evaluate_case_policy_violation(self):
        evaluator = Evaluator(agent_name="test", model="mock")
        case = EvalCase(
            id="test-003",
            name="Policy violation",
            description="Violation",
            input="Do something",
            expected_tools=["get_plan"],
            allowed_tools=["get_plan"],
        )

        def mock_agent(input_text: str) -> dict:
            return {"tools_used": ["delete_plan"], "output": {}, "tokens_used": 50}

        result = evaluator.evaluate_case(case, mock_agent)
        assert result.policy_violations > 0

    def test_evaluate_case_agent_error(self):
        evaluator = Evaluator(agent_name="test", model="mock")
        case = EvalCase(
            id="test-004",
            name="Agent error",
            description="Error",
            input="Bad",
            expected_tools=["get_plan"],
        )

        def failing_agent(input_text: str) -> dict:
            raise ValueError("LLM timeout")

        result = evaluator.evaluate_case(case, failing_agent)
        assert result.success is False
        assert result.error is not None

    def test_run_full_evaluation(self):
        evaluator = Evaluator(agent_name="test-agent", model="mock")
        cases = get_planning_agent_cases()[:2]

        call_count = 0

        def mock_agent(input_text: str) -> dict:
            nonlocal call_count
            call_count += 1
            return {
                "tools_used": ["create_scenario"],
                "output": {"scenario_id": "test", "status": "created"},
                "tokens_used": 100,
            }

        report = evaluator.run_evaluation(cases, mock_agent)
        assert isinstance(report, EvalReport)
        assert report.total_cases == 2
        assert report.agent_name == "test-agent"
        assert call_count == 2

    def test_generate_markdown_report(self):
        evaluator = Evaluator(agent_name="test", model="mock")
        case = EvalCase(
            id="md-001",
            name="Markdown test",
            description="Test",
            input="Test",
            expected_tools=["get_plan"],
        )

        def mock_agent(input_text: str) -> dict:
            return {"tools_used": ["get_plan"], "output": {}, "tokens_used": 10}

        report = evaluator.run_evaluation([case], mock_agent)
        md = evaluator.generate_markdown(report)
        assert "# Evaluation Report" in md
        assert "| Total Cases |" in md
