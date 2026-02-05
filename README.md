# Cohere Math Agent

An AI agent system for solving IMO and Putnam problems, inspired by the IMO25 project but implemented with modern software engineering practices and supporting multiple LLM backends (Cohere, OpenAI, Anthropic, Gemini, DeepSeek, OpenRouter).

## Setup

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
    COHERE_API_KEY=your_cohere_key
    OPENAI_API_KEY=your_openai_key
    ANTHROPIC_API_KEY=your_anthropic_key
    GOOGLE_API_KEY=your_google_key
    DEEPSEEK_API_KEY=your_deepseek_key
    OPENROUTER_API_KEY=your_openrouter_key
    ```

## Usage

Run the agent using the CLI:

```bash
uv run mo-agent example_problem.txt --backend cohere
```

You can also use `uv run python main.py` directly:

```bash
uv run python main.py problem.txt --backend cohere
```

### Options

*   `--backend`, `-b` (Default: `cohere`): Choose the backend for solving (`cohere`, `openai`, `anthropic`, `gemini`, `deepseek`, or `openrouter`).
*   `--model`, `-m`: Specify a specific model for solving.
*   `--v-backend`: Choose a different backend for verification.
*   `--v-model`: Specify a different model for verification.
*   `--max-runs` (Default: 10): Maximum number of full attempts.
*   `--output`: File to save the final solution.
*   `--solver-temp` (Default: 0.7): Temperature for solver model.
*   `--verifier-temp` (Default 0.1): Temperature for verifier model.

### Examples

**Use Cohere for solving with a specific model for verification:**
```bash
uv run mo-agent problem.txt -b cohere --v-model command-r-08-2024
```

**Use OpenAI for solving and Anthropic for verification:**
```bash
uv run mo-agent problem.txt -b openai --v-backend anthropic
```

## Architecture

*   **`src/math_agent/cli.py`**: CLI entry point.
*   **`src/math_agent/agent.py`**: Core agent logic (Initial Solution -> Self-Improvement -> Verification Loop).
*   **`src/math_agent/backends/`**: Backends for different LLM providers.
*   **`src/math_agent/prompts.py`**: Prompts for solving and verification.
