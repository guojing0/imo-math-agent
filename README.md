# Cohere Math Agent

An AI agent system for solving IMO and Putnam problems, inspired by the IMO25 project but implemented with modern software engineering practices and supporting multiple LLM backends (Cohere, OpenAI, Anthropic, Gemini).

## Setup

This project uses `uv` for dependency management.

1.  **Install uv:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    ```

3.  **Environment Variables:**
    Create a `.env` file in the root directory and add your API keys:
    ```bash
    CO_API_KEY=your_cohere_key
    OPENAI_API_KEY=your_openai_key
    ANTHROPIC_API_KEY=your_anthropic_key
    GOOGLE_API_KEY=your_google_key
    ```

## Usage

Run the agent using the CLI:

```bash
uv run python main.py problem.txt --backend cohere
```

### Options

*   `--backend`, `-b`: Choose the backend for solving (`cohere`, `openai`, `anthropic`, `gemini`). Default is `cohere`.
*   `--model`, `-m`: Specify a model name for solving. Defaults to backend-specific best model.
*   `--v-backend`: Choose a different backend for verification.
*   `--v-model`: Specify a different model name for verification.
*   `--max-runs`: Maximum number of full attempts (outer loop). Default is 10.
*   `--output`: File to save the final solution.
*   `--other-prompts`: Additional prompts or hints (comma-separated).

### Examples

**Use Cohere Command R Plus for solving and Command R for verification:**
```bash
uv run python main.py problem.txt -b cohere -m command-r-plus --v-model command-r-08-2024
```

**Use OpenAI GPT-4o for solving and Claude 3.5 Sonnet for verification:**
```bash
uv run python main.py problem.txt -b openai -m gpt-4o --v-backend anthropic --v-model claude-3-5-sonnet-20240620
```

## Architecture

*   **`src/math_agent/agent.py`**: Core agent logic (Initial Solution -> Self-Improvement -> Verification Loop).
*   **`src/math_agent/backends/`**: Modular backend system for different LLM providers.
*   **`src/math_agent/prompts.py`**: System prompts for solving and verification.

## Testing

Run unit tests:
```bash
PYTHONPATH=src uv run python -m unittest tests/test_agent.py
```
