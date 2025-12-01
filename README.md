# AudAgent

A visualized privacy auditing tool for AI agents.

<p align="center">
    <img src="/others/demo_disclosure_violation.gif" alt="Demonstration" width="1080"/>
</p>

⚠️ This project is still a work in progress. Some features may be incomplete or contain errors.

## Installation

This project was developed with Python 3.13 and uses `uv` for package management. Ensure you have `uv` installed.

To install the required dependencies (in `pyproject.toml`), cd to the root directory and run:

```bash
uv pip install .
```

The visualization frontend requires the Node.js (tested on v22.20.0) environment. Make sure you have it installed.

To install the required dependencies for the frontend, navigate to the `audagent/visualization/frontend` directory and run:

```bash
npm install
```

This will install all necessary packages listed in `package.json`.

## Usage

The workflow of AudAgent consists of two main steps: (i) running the visualization frontend to wait for streaming data, and (ii) running the agent process to perform privacy auditing and send data to the frontend.

### 1. Start the Visualization Frontend

To start the AudAgent visualization frontend, navigate to the `audagent/` directory and run: (see `cli.py` for details)

```bash
uv run ./cli.py ui
```

This will build the frontend (if you haven't built it before) and start a local server. 
You will see a message indicating the server is running, typically at `http://localhost:5173`. 
Generally, this URL will be opened automatically in your web browser to access the AudAgent interface.

### 2. Run the Agent Process

To run the agent process along with privacy auditing, you can follow one of the provided example scripts or create your own.
For example, to reproduce the demonstration shown in the GIF above, navigate to the `examples/` directory and run:

```bash
uv run ./personal_email_disclosure.py
```

This is an AI agent with three search tools, along with AudAgent module plug-in for privacy auditing and visualization.
You will see the agent waiting for your input in the terminal.
Type the following query and press Enter:

```text
My friend Bob, who lives in New York City, worked there before. His email address is bob@gmail.com; can you search him and summarize his information for a contact record?
```

The agent will process your query, and you can observe the privacy auditing process in real-time on the AudAgent visualization interface in your web browser.

## Customization

You can customize the agent, tools, and auditing policies according to your needs. 
Refer to the example `examples/personal_email_disclosure.py` directory for guidance on how to set up your own agent and privacy policies.

More specifically, the AudAgent module is plugged into the agent using the following code snippet:

```python
# --- Initialize Audagent with privacy policy ---
PRIVACY_PATH = (Path(__file__).resolve().parent / ".." / "privacy_policy" / "anthropic" / "simplified_privacy_model.json").resolve()
os.environ["AUDAGENT_PRIVACY_POLICIES"] = str(PRIVACY_PATH)
import audagent
# --- End of Audagent initialization ---
```
You only need to provide the path to your privacy policy file (analyzed by LLMs into a JSON model in this paper) and import the `audagent` module to enable privacy auditing and visualization.
It is independent of the agent and tools.
