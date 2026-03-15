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
    help="Path to your solution file",
)
def start(file: Path) -> None:
    from tcode.config import SessionConfig
    from tcode.session import SessionApp
    from tcode.tui import TCodeApp

    watch_path = file.expanduser().resolve()

    problem_id = TCodeApp(watch_path=watch_path).run()
    if not problem_id:
        return  # user quit/cancelled in menu

    config = SessionConfig(problem_id=str(problem_id))
    SessionApp(watch_path=watch_path, config=config).run()


if __name__ == "__main__":
    cli()
