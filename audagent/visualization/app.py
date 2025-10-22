import asyncio

import uvicorn

from audagent.visualization.consts import VISUALIZATION_SERVER_PORT


async def run_fastapi(server_path: str = "server:app") -> None:
    """Run FastAPI server asynchronously"""
    config = uvicorn.Config(server_path, host="127.0.0.1", port=VISUALIZATION_SERVER_PORT, log_level="error")
    server = uvicorn.Server(config)
    print(f"Running UI http://localhost:{VISUALIZATION_SERVER_PORT}/ui")
    await server.serve()

async def main() -> None:
    """Run FastAPI and Streamlit concurrently"""
    await run_fastapi()

if __name__ == "__main__":
    asyncio.run(main())
