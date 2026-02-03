import os
import typer
import logging
from typing import Optional
from dotenv import load_dotenv
from math_agent.agent import MathAgent
from math_agent.backends import CohereBackend, OpenAIBackend, AnthropicBackend, GeminiBackend

# Load environment variables
load_dotenv()

app = typer.Typer()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_backend(backend_name: str, model_name: Optional[str] = None):
    if backend_name == "cohere":
        return CohereBackend(model=model_name or "command-r-08-2024")
    elif backend_name == "openai":
        return OpenAIBackend(model=model_name or "gpt-4o")
    elif backend_name == "anthropic":
        return AnthropicBackend(model=model_name or "claude-3-5-sonnet-20240620")
    elif backend_name == "gemini":
        return GeminiBackend(model=model_name or "gemini-1.5-pro")
    else:
        raise ValueError(f"Unknown backend: {backend_name}")

@app.command()
def main(
    problem_file: str = typer.Argument(..., help="Path to the problem statement file."),
    backend: str = typer.Option("cohere", "-b", "--backend", help="Backend to use for solving: cohere, openai, anthropic, gemini"),
    model: Optional[str] = typer.Option(None, "-m", "--model", help="Model name for solving. Defaults to backend specific best model."),
    verifier_backend: Optional[str] = typer.Option(None, "--v-backend", help="Backend to use for verification. Defaults to the same as solver backend."),
    verifier_model: Optional[str] = typer.Option(None, "--v-model", help="Model name for verification. Defaults to solver model or backend default."),
    max_runs: int = typer.Option(10, help="Maximum number of full attempts."),
    output: Optional[str] = typer.Option(None, help="File to save the solution."),
    other_prompts: Optional[str] = typer.Option(None, help="Comma-separated list of other prompts.")
):
    """
    Math Agent CLI for solving IMO/Putnam problems.
    """
    
    logger.info(f"Solver Backend: {backend}, Model: {model or 'default'}")
    if verifier_backend or verifier_model:
        logger.info(f"Verifier Backend: {verifier_backend or backend}, Model: {verifier_model or model or 'default'}")

    try:
        # Read problem
        with open(problem_file, 'r', encoding='utf-8') as f:
            problem_statement = f.read()
    except FileNotFoundError:
        logger.error(f"Problem file not found: {problem_file}")
        raise typer.Exit(code=1)

    # Prepare other prompts
    prompts_list = other_prompts.split(',') if other_prompts else []

    # Initialize Backends
    try:
        solver_llm = get_backend(backend, model)
        
        if verifier_backend or verifier_model:
            v_backend_name = verifier_backend or backend
            verifier_llm = get_backend(v_backend_name, verifier_model)
        else:
            verifier_llm = solver_llm
            
    except Exception as e:
        logger.error(f"Failed to initialize backend: {e}")
        raise typer.Exit(code=1)

    # Initialize Agent
    agent = MathAgent(backend=solver_llm, verifier_backend=verifier_llm)

    # Outer Loop
    success = False
    final_solution = None

    for i in range(max_runs):
        logger.info(f"========== Full Attempt {i+1}/{max_runs} ==========")
        solution = agent.solve(problem_statement, other_prompts=prompts_list)
        
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
            with open(output, 'w', encoding='utf-8') as f:
                f.write(final_solution)
            logger.info(f"Solution saved to {output}")
    else:
        logger.error("Failed to find a solution after all attempts.")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
