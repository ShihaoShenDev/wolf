import typer
import uvicorn

app = typer.Typer()

@app.command()
def server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    Start the Wolf server.
    """
    typer.echo(f"Starting server at {host}:{port}")
    uvicorn.run("wolf.server.app:app", host=host, port=port, reload=reload)

@app.command()
def client():
    """
    Start the Wolf client.
    """
    typer.echo("Starting client...")
    from wolf.client import cli_client
    cli_client.run()

if __name__ == "__main__":
    app()
