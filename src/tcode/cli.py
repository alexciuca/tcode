from pathlib import Path

import click


@click.group()
def cli() -> None:
    """tcode - terminal coding tutor"""


@cli.command()
@click.option(
    "--file",
    "-f",
    required=True,
    type=click.Path(path_type=Path),
    help="Path to your solution file. Created with starter code if missing.",
)
def start(file: Path) -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from tcode.config import SessionConfig
    from tcode.problems import load_problem_by_id
    from tcode.session import SessionApp
    from tcode.solution_file import write_starter_code_if_needed
    from tcode.tui import TCodeApp

    watch_path = file.expanduser().resolve()

    problem_id = TCodeApp(watch_path=watch_path).run()
    if not problem_id:
        return  # user quit/cancelled in menu

    problem = load_problem_by_id(str(problem_id))
    write_starter_code_if_needed(watch_path, problem.starter_code)

    config = SessionConfig(problem_id=str(problem_id))
    SessionApp(watch_path=watch_path, config=config).run()


if __name__ == "__main__":
    cli()
