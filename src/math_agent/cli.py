import logging
from typing import Optional

import typer
from dotenv import load_dotenv

from math_agent.agent import MathAgent
from math_agent.backends.registry import get_backend
from math_agent.config import AgentConfig

# Load environment variables
load_dotenv()

app = typer.Typer()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@app.command()
def main(
    problem_file: str = typer.Argument(..., help="Path to the problem statement file."),
    backend: str = typer.Option(
        "cohere",
        "-b",
        "--backend",
        help=f"Backend to use for solving: cohere, openai, anthropic, gemini, deepseek, openrouter",
    ),
    model: Optional[str] = typer.Option(
        None,
        "-m",
        "--model",
        help="Model name for solving. Defaults to backend specific best model.",
    ),
    verifier_backend: Optional[str] = typer.Option(
        None,
        "--v-backend",
        help="Backend to use for verification. Defaults to the same as solver backend.",
    ),
    verifier_model: Optional[str] = typer.Option(
        None,
        "--v-model",
        help="Model name for verification. Defaults to solver model or backend default.",
    ),
    max_runs: int = typer.Option(10, help="Maximum number of full attempts."),
    output: Optional[str] = typer.Option(None, help="File to save the solution."),
    solver_temperature: float = typer.Option(
        0.7, "--solver-temp", help="Temperature for solver model."
    ),
    verifier_temperature: float = typer.Option(
        0.1, "--verifier-temp", help="Temperature for verifier model."
    ),
):
    """
    Math Agent CLI for solving IMO/Putnam problems.
    """

    logger.info(f"Solver Backend: {backend}, Model: {model or 'default'}")
    if verifier_backend or verifier_model:
        logger.info(
            f"Verifier Backend: {verifier_backend or backend}, "
            f"Model: {verifier_model or model or 'default'}"
        )

    try:
        with open(problem_file, "r", encoding="utf-8") as f:
            problem_statement = f.read()
    except FileNotFoundError:
        logger.error(f"Problem file not found: {problem_file}")
        raise typer.Exit(code=1)

    # Create config with CLI overrides
    config = AgentConfig(
        solver_temperature=solver_temperature,
        verifier_temperature=verifier_temperature,
    )

    # Initialize backends using registry
    try:
        solver_llm = get_backend(backend, model, config)

        if verifier_backend or verifier_model:
            v_backend_name = verifier_backend or backend
            verifier_llm = get_backend(v_backend_name, verifier_model, config)
        else:
            verifier_llm = solver_llm

    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise typer.Exit(code=1)

    # Initialize Agent
    agent = MathAgent(backend=solver_llm, verifier_backend=verifier_llm, config=config)

    # Outer Loop
    success = False
    final_solution = None

    for i in range(max_runs):
        logger.info(f"========== Full Attempt {i+1}/{max_runs} ==========")
        solution = agent.solve(problem_statement)

        if solution:
            logger.info("Found a correct solution!")
            final_solution = solution
            success = True
            break
        else:
            logger.info("Attempt failed. Retrying...")

    if success and final_solution:
        print("\n\nFINAL SOLUTION:\n")
        print(final_solution)
        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(final_solution)
            logger.info(f"Solution saved to {output}")
    else:
        logger.error("Failed to find a solution after all attempts.")
        raise typer.Exit(code=1)
