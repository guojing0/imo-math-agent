import unittest
from unittest.mock import MagicMock

from math_agent.agent import MathAgent
from math_agent.backends.base import LLMBackend
from math_agent.config import AgentConfig


class TestMathAgent(unittest.TestCase):
    def setUp(self):
        self.mock_backend = MagicMock(spec=LLMBackend)
        # Set config attribute on mock
        self.mock_backend.config = AgentConfig()
        self.config = AgentConfig(
            required_consecutive_validations=5,
            max_consecutive_errors=10,
        )
        self.agent = MathAgent(
            backend=self.mock_backend,
            config=self.config,
        )

    def test_solve_success_first_try(self):
        # Setup mock responses
        # Sequence:
        # 1. Initial Exploration -> Sol1
        # 2. Self Improvement -> Sol2
        # 3. Verification Log (Verifier) -> Log
        # 4. Check Verification (Verifier -> "yes")
        # ... repeat verify 4 more times ...

        def side_effect(*args, **kwargs):
            system_prompt = kwargs.get("system_prompt", "")
            user_prompt = kwargs.get("user_prompt", "")

            if "Core Instructions" in system_prompt:  # Step 1 or Improvement
                return "Mock Solution"
            elif "act as an IMO grader" in system_prompt:  # Verification
                return "Detailed Verification Log: Correct."
            elif 'Response in "yes" or "no"' in user_prompt:  # Check validity
                return "yes"
            else:
                return "Generic Response"

        self.mock_backend.generate.side_effect = side_effect

        solution = self.agent.solve("Problem Statement", max_iterations=10)

        self.assertEqual(solution, "Mock Solution")
        # Init(1) + Imp(1) + 5 * (Verify(1) + Check(1)) = 12
        self.assertTrue(self.mock_backend.generate.call_count >= 12)

    def test_solve_failure_verification(self):
        # Mock always failing verification
        def side_effect(*args, **kwargs):
            user_prompt = kwargs.get("user_prompt", "")
            if 'Response in "yes" or "no"' in user_prompt:
                return "no"
            return "Solution"

        self.mock_backend.generate.side_effect = side_effect

        solution = self.agent.solve("Problem", max_iterations=5)
        self.assertIsNone(solution)


class TestVerificationParsing(unittest.TestCase):
    def test_exact_yes(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response("yes")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_exact_no(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response("no")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.confidence, 1.0)

    def test_starts_with_yes(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response("Yes, the solution is correct.")
        self.assertTrue(result.is_valid)
        self.assertGreaterEqual(result.confidence, 0.8)

    def test_starts_with_no(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response("No, there are errors in the proof.")
        self.assertFalse(result.is_valid)
        self.assertGreaterEqual(result.confidence, 0.8)

    def test_keyword_analysis_positive(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response(
            "The solution is correct and valid. No errors found."
        )
        self.assertTrue(result.is_valid)

    def test_keyword_analysis_negative(self):
        from math_agent.verification import parse_verification_response

        result = parse_verification_response(
            "The solution contains an error and has a gap in the reasoning."
        )
        self.assertFalse(result.is_valid)


class TestAgentConfig(unittest.TestCase):
    def test_default_values(self):
        config = AgentConfig()
        self.assertEqual(config.solver_temperature, 0.7)
        self.assertEqual(config.verifier_temperature, 0.1)
        self.assertEqual(config.max_verification_iterations, 30)
        self.assertEqual(config.required_consecutive_validations, 5)
        self.assertEqual(config.max_consecutive_errors, 10)
        self.assertEqual(config.max_tokens, 8192)
        self.assertEqual(config.retry_attempts, 3)

    def test_custom_values(self):
        config = AgentConfig(
            solver_temperature=0.5,
            verifier_temperature=0.2,
            max_verification_iterations=20,
        )
        self.assertEqual(config.solver_temperature, 0.5)
        self.assertEqual(config.verifier_temperature, 0.2)
        self.assertEqual(config.max_verification_iterations, 20)

    def test_frozen(self):
        config = AgentConfig()
        with self.assertRaises(Exception):  # FrozenInstanceError
            config.solver_temperature = 0.5


if __name__ == "__main__":
    unittest.main()
