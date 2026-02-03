import unittest
from unittest.mock import MagicMock
from math_agent.agent import MathAgent
from math_agent.backends.base import LLMBackend

class TestMathAgent(unittest.TestCase):
    def setUp(self):
        self.mock_backend = MagicMock(spec=LLMBackend)
        self.agent = MathAgent(backend=self.mock_backend)

    def test_solve_success_first_try(self):
        # Setup mock responses
        # 1. Initial exploration -> "Solution"
        # 2. Self improvement -> "Improved Solution"
        # 3. Verification -> "Verification Log... Summary: Correct" (Checking "yes")
        
        # Responses for generate calls:
        # Call 1: Initial Exploration
        # Call 2: Self Improvement
        # Call 3: Verification Log (Verifier)
        # Call 4: Check Verification (Verifier -> "yes")
        
        # But wait, verification loop repeats until correct_count >= 5.
        # So we need 5 consecutive correct verifications.
        # Sequence:
        # 1. Init -> Sol1
        # 2. Improve -> Sol2
        # 3. Verify(Sol2) -> Log1
        # 4. Check(Log1) -> "yes"
        # ... repeat verify 4 more times ...
        
        # Let's simplify and mock generate to return specific things based on input prompts or just sequence.
        
        def side_effect(*args, **kwargs):
            system_prompt = kwargs.get('system_prompt', '')
            user_prompt = kwargs.get('user_prompt', '')
            
            if "Core Instructions" in system_prompt: # Step 1 or Improvement
                return "Mock Solution"
            elif "act as an IMO grader" in system_prompt: # Verification
                return "Detailed Verification Log: Correct."
            elif "Response in \"yes\" or \"no\"" in user_prompt: # Check validity
                return "yes"
            else:
                return "Generic Response"

        self.mock_backend.generate.side_effect = side_effect

        solution = self.agent.solve("Problem Statement", max_iterations=10)
        
        self.assertEqual(solution, "Mock Solution")
        self.assertTrue(self.mock_backend.generate.call_count >= 12) # Init(1) + Imp(1) + 5 * (Verify(1) + Check(1)) = 12

    def test_solve_failure_verification(self):
        # Mock always failing verification
        def side_effect(*args, **kwargs):
            if "Response in \"yes\" or \"no\"" in user_prompt:
                return "no"
            return "Content"
            
        self.mock_backend.generate.return_value = "no" # Simplistic
        
        # We need more granular control to avoid infinite loops or confusing logic if "no" is returned for everything.
        # Let's just set side_effect for the check only.
        
        def side_effect(*args, **kwargs):
            user_prompt = kwargs.get('user_prompt', '')
            if "Response in \"yes\" or \"no\"" in user_prompt:
                return "no"
            return "Solution"

        self.mock_backend.generate.side_effect = side_effect
        
        solution = self.agent.solve("Problem", max_iterations=5)
        self.assertIsNone(solution)

if __name__ == '__main__':
    unittest.main()
