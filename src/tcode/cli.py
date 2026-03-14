from pathlib import Path
import click 

@click.group()
def cli() -> None:
    """tcode - terminal coding tutor"""

@cli.command()
@click.option("--file", "-f", required=True, type=click.Path(), help="Path to your solution file")
def start(file: str) -> None:
    from tcode.config import SessionConfig
    from tcode.tui import TCodeApp
    TCodeApp().run()

if __name__ == "__main__":
    cli()
