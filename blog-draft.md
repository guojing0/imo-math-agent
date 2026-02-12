# Building a Multi-LLM Agent That Solves Competition Math Problems

Can we build a system that reliably solves IMO and Putnam-level math problems - not by getting lucky on a single forward pass, but by iterating toward a correct, rigorous proof? That's the question behind this project. Inspired by the IMO25 challenge and the growing interest in LLM-based mathematical reasoning, I built a solver-verifier agent that combines multiple LLMs in a generate-critique-refine loop. This post walks through the architecture, the key design decisions, and what I learned along the way.

## The Problem

Competition math is one of the hardest benchmarks for LLMs. These problems - from the International Mathematical Olympiad, Putnam, and similar competitions - demand multi-step deductive reasoning, creative constructions, and airtight logical rigor. Pattern matching is not enough.

The core difficulty is that LLMs hallucinate reasoning steps. They produce proofs that *look* correct - the notation is right, the structure feels plausible - but contain subtle logical gaps or outright errors buried in the middle. A model might claim "by interchanging the limit and the integral" without verifying uniform convergence, or assert that $A > B$ and $C > D$ implies $A - C > B - D$ (it doesn't). The output reads like a proof, but it isn't one.

A single forward pass simply cannot be trusted. What we need instead is an iterative system: one that generates candidate solutions, critiques them for errors, and refines them until the proof is genuinely sound. That's the agent I built.

## Architecture Overview

The system follows a four-phase loop:

```
Problem
  |
  v
[1] Initial Exploration  (solver LLM, temp=0.7)
  |
  v
[2] Self-Improvement      (solver LLM, temp=0.7)
  |
  v
[3] Verification           (verifier LLM, temp=0.1)
  |
  +--- Valid? ---> increment streak counter
  |                   |
  |                   +--- 5 consecutive passes ---> SUCCESS
  |
  +--- Invalid? -> Bug Report -> [4] Correction -> back to [3]
                                   |
                                   +--- 10 consecutive errors -> FAILURE
```

The solver and verifier can be different models running on different backends. This separation is fundamental - you want creative, exploratory generation on the solving side, and strict, conservative evaluation on the verification side.

Here are the key configuration values that govern the loop:

```python
@dataclass(frozen=True)
class AgentConfig:
    solver_temperature: float = 0.7     # Creative solving
    verifier_temperature: float = 0.1   # Strict verification
    max_verification_iterations: int = 20
    required_consecutive_validations: int = 5
    max_consecutive_errors: int = 10
```

**Why 5 consecutive validations?** A single verification pass is unreliable. LLMs can miss errors, especially subtle ones. Requiring 5 consecutive "valid" verdicts dramatically reduces the probability of a flawed proof slipping through - if there's a real bug, at least one of the 5 passes will likely catch it.

**Why 10 consecutive errors as the bail-out?** If the agent has failed to produce a valid solution after 10 correction attempts in a row, the current line of reasoning is probably unsalvageable. Better to fail fast (and let the outer retry loop start from scratch) than to keep polishing a fundamentally broken approach.

The outer loop in `main.py` wraps the entire solve cycle with up to 10 full independent attempts, giving the agent multiple fresh starts at the problem.

## The Verification Strategy

Verification is the most technically interesting part of the system, and the part I spent the most time on. Getting it right matters enormously: a verifier that's too lenient will pass broken proofs, and one that's too strict will reject correct solutions and trap the agent in an infinite correction loop.

### Two-Phase Verification

Verification happens in two steps. First, the verifier LLM generates a detailed verification log - it's prompted to act as an IMO grader performing a step-by-step audit of the proof. Second, a follow-up call distills that log into a binary yes/no judgment.

```python
# Step 1: Full verification log
verification_log = self.verifier_backend.generate(
    system_prompt=VERIFICATION_SYSTEM_PROMPT,
    user_prompt=verification_prompt,
    temperature=0.1,
)

# Step 2: Binary distillation
check_prompt = (
    'Response in "yes" or "no". '
    "Is the following statement saying the solution is correct, "
    "or does not contain critical error or a major justification gap?\n\n"
    f"{verification_log}"
)
check_response = self.verifier_backend.generate(
    system_prompt="",
    user_prompt=check_prompt,
    temperature=0.1,
)
```

Why two phases instead of one? Because asking an LLM to simultaneously reason about a proof's correctness *and* produce a clean boolean verdict leads to worse results on both counts. The two-phase approach lets the model think deeply in the first pass, then make a focused judgment call in the second.

### Prompt Design for the Verifier

The verification system prompt carefully distinguishes between two categories of issues:

- **Critical Errors** break the logical chain. A calculation mistake, a logical fallacy, an invalid inference. If the verifier finds one, it stops checking dependent steps (but still scans for independent parts of the proof).
- **Justification Gaps** are places where the conclusion might be correct but the argument is incomplete or hand-wavy. The verifier notes the gap, assumes the conclusion is true for the sake of argument, and continues checking the rest.

This distinction matters because a proof with a few minor justification gaps might still be essentially correct, while a single critical error is fatal. The verifier's summary format makes this explicit - every finding is tagged with its category and a location quote from the original proof.

### Robust Response Parsing

The binary yes/no check sounds simple, but LLMs are notoriously bad at following instructions to produce minimal output. Instead of a clean "yes" or "no", you get responses like "Yes, the solution appears to be correct" or "No, as detailed above, the proof contains a critical error in step 3."

The parser in `verification.py` handles this with a layered approach:

1. **Exact match** - if the response is literally "yes" or "no"
2. **Boundary match** - if the response starts or ends with "yes"/"no"
3. **Keyword analysis** - count positive patterns (`\bcorrect\b`, `\bvalid\b`, `\bno errors?\b`) against negative patterns (`\berror\b`, `\bflaw\b`, `\bgap\b`, `\bwrong\b`) and go with the majority
4. **Fallback containment** - check if only "yes" or only "no" appears anywhere in the text
5. **Safe default** - if everything is ambiguous, default to **invalid**

That last point is a deliberate design choice. When verification is genuinely ambiguous, it's safer to assume the proof has issues and trigger another correction cycle than to prematurely accept a flawed solution.

## Multi-Backend Design

The agent supports four LLM providers - Cohere, OpenAI, Anthropic, and Google (Gemini) - through an abstract backend system. The core abstraction is an `LLMBackend` base class that handles retry logic with exponential backoff, while each provider subclass implements the actual API call:

```python
class LLMBackend(ABC):
    def generate(self, system_prompt, user_prompt, other_prompts=None, temperature=0.7):
        for attempt in range(self.config.retry_attempts):
            try:
                return self._generate_impl(system_prompt, user_prompt, other_prompts, temperature)
            except Exception as e:
                delay = self.config.retry_base_delay * (2 ** attempt)
                time.sleep(delay)
        raise last_exception

    @abstractmethod
    def _generate_impl(self, ...): ...
```

A registry pattern provides factory-based backend creation with sensible defaults:

```python
DEFAULT_MODELS = {
    "cohere": "command-a-reasoning-08-2025",
    "openai": "gpt-5.2-2025-12-11",
    "anthropic": "claude-sonnet-4-5",
    "gemini": "gemini-2.5-pro",
}
```

Each provider has its quirks. Cohere's reasoning models return a mix of `thinking` and `text` content blocks - you need to filter out the thinking blocks to get the actual response. Anthropic requires alternating user/assistant roles in the message sequence, so consecutive user messages must be merged. Gemini uses its own `Content`/`Part` type system with different role names (`"model"` instead of `"assistant"`). The base class provides a `merge_consecutive_messages` utility that subclasses can use when their API demands it.

The practical payoff: you can use one model for solving and a completely different one for verification. Run your solver on a strong reasoning model and your verifier on a different provider entirely. From the CLI:

```bash
uv run python main.py problem.txt \
    --backend cohere --model command-a-reasoning-08-2025 \
    --v-backend anthropic --v-model claude-sonnet-4-5
```

## Walkthrough: Solving a Problem

Here's how the agent tackles a problem end to end. Say we feed it a number theory problem from a recent competition.

**Phase 1 - Initial Exploration.** The solver receives the problem with instructions to produce a structured response: a summary with a verdict and method sketch, followed by a full detailed solution. The solver temperature is 0.7 - warm enough to explore creative approaches.

**Phase 2 - Self-Improvement.** The agent feeds the initial solution back to the same solver along with a self-improvement prompt: "You have an opportunity to improve your solution. Review it carefully. Correct errors and fill justification gaps if any." This catches the low-hanging fruit - obvious mistakes, places where the model "knew" the step was weak.

**Phase 3 - Verification.** The detailed solution (extracted automatically from the structured output) goes to the verifier. The verifier walks through the proof step by step, producing a log like:

```
Final Verdict: The solution contains a Critical Error and is therefore invalid.

List of Findings:
- Location: "Since $p | a^2$, we have $p | a$ by Euclid's lemma"
  Issue: Justification Gap - Euclid's lemma requires $p$ to be prime,
  which has not been established at this point in the proof.
```

The binary check returns "no", and the full verification log becomes the bug report.

**Phase 4 - Correction.** The solver receives the original problem, its proposed solution, and the bug report. The correction prompt is carefully worded: "If you agree with certain items in the bug report, improve your solution. Note that the evaluator can misunderstand your solution and thus make mistakes. If you disagree with certain items, add detailed explanations to avoid such misunderstanding." This bidirectional framing is important - it prevents the solver from blindly accepting every critique, which could introduce new errors.

The corrected solution goes back to verification. If it passes, the streak counter increments. After 5 consecutive passes, we declare success.

```
Iteration 1/20 - Correct Streak: 0, Errors: 1
Verification failed. Attempting correction...
Iteration 2/20 - Correct Streak: 0, Errors: 0
Solution verified as valid. Streak: 1
...
Iteration 6/20 - Correct Streak: 5, Errors: 0
Solution verified 5 times consecutively. SUCCESS.
```

## Results

**[PLACEHOLDER - To be filled in with:**
- **Problems tested and success rates**
- **Comparison across backends (Cohere, OpenAI, Anthropic, Gemini)**
- **Interesting failure modes or observations**
- **Average number of iterations needed for convergence**
- **Examples of problems solved and problems that stumped the agent]**

## Lessons Learned and What's Next

**Verification is harder than solving.** This was the biggest surprise. Building a good solver is comparatively straightforward - you prompt an LLM to think carefully and it produces reasonable attempts. Building a verifier that reliably distinguishes correct proofs from plausible-looking wrong ones is a much harder problem. The verifier is the true bottleneck of the system.

**Temperature tuning matters more than expected.** Early versions used the same temperature for both roles. Dropping the verifier to 0.1 while keeping the solver at 0.7 made a noticeable difference - the verifier became more consistent and less prone to "creative" reinterpretations of flawed steps.

**Default to "invalid" on ambiguity.** When the verification response is genuinely unclear, rejecting the solution is the right call. The cost of a false rejection is just another iteration. The cost of a false acceptance is a wrong answer presented with misplaced confidence.

**The correction prompt needs to be bidirectional.** Early versions told the solver to "fix the issues in the bug report." This sometimes made things worse - the solver would break a correct step while trying to address a false positive from the verifier. Framing it as "agree or disagree, then act accordingly" produces better results.

Looking ahead, there are several clear directions. Code execution for numeric verification would let the agent check computational claims directly rather than reasoning about them. A fine-tuned verifier model trained specifically on proof checking could dramatically improve accuracy. And integrating tool use - symbolic algebra, automated theorem provers - could extend the system's reach to problems that require heavy computation alongside reasoning.

The code is available at [repository link]. Contributions and feedback are welcome.
