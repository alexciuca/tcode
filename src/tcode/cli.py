from pathlib import Path
import click 

@click.group()
def cli() -> None:
    """tcode - terminal coding tutor"""

@cli.command()
@click.option("--file", "-f", required=True, type=click.Path(), help="Path to your solution file")
def start(file: str) -> None:
    from tcode.tui import TCodeApp
    TCodeApp().run()

# Guard to prevent imports used in other files to execute the whole cli
if __name__ == "__main__":
    cli()
