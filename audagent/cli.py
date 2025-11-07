"""
AudAgent UI with React Frontend and FastAPI Backend.
========
Usage:
$ python cli.py ui [-r]
to launch the AudAgent UI. Use -r to rebuild the UI.
"""
import os
import shutil
import sys
import logging
import argparse
import asyncio
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from audagent.utils.custom_logging_formatter import setup_logging
setup_logging(logging.DEBUG)
logging.getLogger()

from audagent.visualization.app import run_fastapi
from audagent.visualization.consts import VISUALIZATION_SERVER_PORT
from audagent.consts import AUDAGENT_INTERNAL
os.environ[AUDAGENT_INTERNAL] = "1" # Set running flag for AudAgent


async def run_server() -> None:
    try:
        tasks = [run_fastapi("audagent.visualization.server:app")]
        await asyncio.sleep(1.0)
        webbrowser.open_new_tab(f"http://localhost:{VISUALIZATION_SERVER_PORT}/ui")
        await asyncio.gather(*tasks)
    except Exception:
        pass

def run_ui(args: argparse.Namespace) -> None:
    dist_folder = Path(__file__).parent / "visualization" / "frontend" / "dist"
    if args.rebuild:
        if dist_folder.exists():
            shutil.rmtree(str(dist_folder))

    if not dist_folder.exists():
        print("Building UI for the first time...")
        try:
            extra_args: dict[str, Any] = {"capture_output": True}
            if os.name == "nt":
                extra_args["shell"] = True
                extra_args["check"] = True
            subprocess.run(["npm", "i"], cwd=Path(__file__).parent / "visualization" / "frontend", **extra_args)
            subprocess.run(["npm", "run", "build"], cwd=Path(__file__).parent / "visualization" / "frontend", **extra_args)
        except FileNotFoundError:
            print("NPM not found. Please install Node.js and NPM.")
            return
        except Exception as e:
            print(f"Error: {e}")
            return

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass
    
def main() -> None:
    parser = argparse.ArgumentParser(prog="AudAgent", description="AudAgent - A privacy auditor framework for AI agents.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # UI Command
    ui_parser = subparsers.add_parser("ui", help="Launch (and build, if necessary) the AudAgent UI")
    ui_parser.add_argument('-r', '--rebuild', action='store_true', help='Rebuilds the UI')

    ui_parser.set_defaults(func=run_ui)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()
