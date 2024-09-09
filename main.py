import uvicorn
import typer
from controller import app, chat, controller

cli = typer.Typer()

@cli.command()
def run_server():
    """Run the FastAPI server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)

@cli.command()
def run_chat():
    """Run the Sonic Pi Controller in CLI mode."""
    chat()

if __name__ == "__main__":
    cli()