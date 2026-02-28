# IMO Math Agent

An agentic system for solving IMO and Putnam-level math problems. It generates solutions, iteratively self-improves them, and verifies correctness - all powered by your choice of LLM backend (Cohere, OpenAI, Anthropic, Gemini).

## How it works

1. **Solve** - the solver LLM generates an initial solution to the problem
2. **Self-improve** - the solver critiques and refines its own solution
3. **Verify** - a verifier LLM checks the solution for correctness
4. **Retry** - if verification fails, the full cycle repeats (up to `--max-runs` attempts)

The solver and verifier can use different backends and models, letting you mix providers for better results.

## Setup

1. **Install uv:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. **Install dependencies:**
    ```bash
    uv sync
    ```

3. **Environment variables:**
    Create a `.env` file with API keys for the backends you want to use:
    ```bash
    COHERE_API_KEY=your_cohere_key
    OPENAI_API_KEY=your_openai_key
    ANTHROPIC_API_KEY=your_anthropic_key
    GOOGLE_API_KEY=your_google_key
    ```
    You only need keys for the backends you plan to use.

## Usage

```bash
uv run imo-agent problem.txt --backend cohere
```

Or via `python main.py`:

```bash
uv run python main.py problem.txt --backend cohere
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `-b`, `--backend` | `cohere` | LLM backend for solving: `cohere`, `openai`, `anthropic`, `gemini` |
| `-m`, `--model` | backend default | Model name for the solver |
| `--v-backend` | same as solver | LLM backend for verification |
| `--v-model` | same as solver | Model name for the verifier |
| `--max-runs` | `10` | Maximum number of full solve/verify attempts |
| `--output` | - | File path to save the final solution |
| `--solver-temp` | `0.7` | Sampling temperature for the solver |
| `--verifier-temp` | `0.1` | Sampling temperature for the verifier |

### Examples

Use different models for solving and verification:
```bash
uv run imo-agent problem.txt -b cohere --v-model command-r-08-2024
```

Mix providers - solve with OpenAI, verify with Anthropic:
```bash
uv run imo-agent problem.txt -b openai --v-backend anthropic
```

Save the solution to a file:
```bash
uv run imo-agent problem.txt -b cohere --output solution.txt
```

## Architecture

```
src/imo_math_agent/
  cli.py          - CLI entry point (Typer)
  agent.py        - Core agent loop: solve -> self-improve -> verify
  config.py       - Agent configuration (temperatures, etc.)
  prompts.py      - Prompt templates for solving and verification
  prompting.py    - Prompt construction utilities
  verification.py - Solution verification logic
  types.py        - Shared type definitions
  utils.py        - General utilities
  backends/
    base.py       - Abstract backend interface
    cohere.py     - Cohere backend
    openai.py     - OpenAI backend
    anthropic.py  - Anthropic backend
    gemini.py     - Google Gemini backend
    registry.py   - Backend discovery and instantiation
```
