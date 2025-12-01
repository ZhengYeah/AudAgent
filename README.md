# AudAgent

A tool for automated and visualized auditing of privacy policy compliance in AI agents

A media post introducing AudAgent is available at: [Are Your AI Agents Keeping Their Promises?](https://paragraph.com/@metaend/are-your-ai-agents-keeping-their-promises)

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

To install the required dependencies for the frontend (in `package.json`), navigate to the `audagent/visualization/frontend` directory and run:

```bash
npm install
```

## Usage

Polished line replacement:

AudAgent's workflow has two main steps: 
1. start the visualization frontend to receive streaming data;
2. run agent processes to automatically perform privacy auditing and stream results to the frontend.

### 1. Start the Visualization Frontend

To start the AudAgent visualization frontend, navigate to the root directory and run:

```bash
uv run ./audagent/cli.py ui
```

This will build the frontend (if you haven't built it before) and start a local server. 
You will see a message indicating the server is running, typically at `http://localhost:5173`. 
Generally, this URL will be opened automatically in your web browser to access the AudAgent interface.

### 2. Run An Agent Process

To run an agent process along with privacy auditing, you can follow one of the provided example scripts or create your own.
For example, to reproduce the demonstration shown in the GIF above, you should first have access to the necessary LLMs (e.g. Claude or GPT).
Please refer to the respective LLM provider's website to obtain one API if you don't have it yet.
After obtaining the API key, put your LLM api key into `examples/.env` file like this:

```text
ANTHROPIC_API_KEY="sk-xxxxxxxx"
OPENAI_API_KEY="sk-proj-xxxxxxxx"
```

Make sure to add the `.env` file to your `.gitignore` to avoid exposing your API keys publicly.
The `.env` info will be automatically loaded by the `dotenv` package when you run the example script.

Then, navigate to the root directory and run the following command:

```bash
uv run ./examples/personal_email_disclosure.py
```

The `personal_email_disclosure.py` example is an AI agent with three search tools, along with AudAgent module plug-in.
You will see the agent waiting for your input in the terminal. Type the following query and press Enter:

```text
My friend Bob, who lives in New York City, worked there before. His email address is bob@gmail.com; can you search him and summarize his information for a contact record?
```

The agent will process your query, and you can observe the privacy auditing process in real-time on the AudAgent visualization interface in your web browser.

## Customization

You can customize the agent and auditing policies according to your needs. 
Refer to the example `examples/personal_email_disclosure.py` for guidance on how to set up your own agent and privacy policies.

More specifically, the AudAgent module is plugged into the agent using the following code snippet:

```python
# --- Initialize Audagent with privacy policy ---
PRIVACY_PATH = (Path(__file__).resolve().parent / ".." / "privacy_policy" / "anthropic" / "simplified_privacy_model.json").resolve()
os.environ["AUDAGENT_PRIVACY_POLICIES"] = str(PRIVACY_PATH)
import audagent
# --- End of Audagent initialization ---
```
You only need to provide the path to your privacy policy file (analyzed by LLMs into a JSON model in this paper) and import the `audagent` module to enable privacy auditing and visualization.
It is independent of the agent, so you can easily integrate it with your own agent implementations.

## Thanks

This project is based on the visualization tool [agentwatch](https://github.com/cyberark/agentwatch) by cyberark, thanks to their great work.
