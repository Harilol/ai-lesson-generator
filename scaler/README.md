# Agentic Lesson Generator

A small Python application that uses LangGraph to generate a beginner-friendly lesson and iteratively review it with an LLM. The generator and evaluator use the same chat model configured through OpenRouter.

## What it does

The application starts with a topic and a target audience, asks the model to write a lesson, and then evaluates that draft against a rubric. When the draft is not approved, the evaluator's feedback is added to the shared workflow state and the generator is asked to revise its lesson.

The example input in `Assessment.py` is:

- **Topic:** RAG (Retrieval-Augmented Generation)
- **Audience:** A 12th-grade graduate in India with a non-English-medium background who is starting an AI career

The script prints the final draft, the number of generation attempts, and the most recent evaluator feedback.

## Agentic workflow

The workflow is implemented as a LangGraph state graph with two nodes and a conditional loop:

```text
START
  |
  v
Generator -- creates or revises a lesson
  |
  v
Evaluator -- checks the draft against the rubric
  |
  +-- approved or attempt limit reached --> END
  |
  +-- not approved -----------------------> Generator
```

### Shared state

The `LessonState` typed dictionary in `Assessment.py` carries information between nodes:

| Field | Purpose |
|---|---|
| `topic` | Subject the lesson should explain. |
| `target_audience` | Reader profile used to tune the lesson's language and examples. |
| `draft` | Latest lesson produced by the generator. |
| `evaluation_feedback` | Latest review response or revision instruction. |
| `passed` | Whether the evaluator approved the current draft. |
| `iteration_count` | Number of lesson drafts generated so far. |

### Nodes and transitions

1. **Generator (`generate_node`)** builds a prompt asking for a beginner-friendly lesson. It requests a relatable analogy, simple English, and a step-by-step explanation of what the topic is, why it matters, and how it works. If feedback exists in the state, that feedback is included in the next prompt. Each generated draft increments `iteration_count`.
2. **Evaluator (`evaluate_node`)** asks the model to assess the draft on four criteria:
   - **Accuracy:** Is the explanation technically correct and on topic?
   - **Analogy:** Does it begin with a clear, relatable real-world analogy?
   - **Simplicity:** Is the vocabulary accessible to the intended audience?
   - **Structure:** Does it explain what, why, and how?
3. **Router (`should_continue`)** ends the workflow if `passed` is true or the iteration count is greater than 3. Otherwise, it routes back to the generator.

### Current retry behavior

The current implementation has a special first-review behavior: after asking the model to evaluate the first draft, it discards that review result, sets `passed` to false, and supplies a fixed instruction to simplify the English. On later attempts, the evaluator's model response is used to determine approval. The workflow can generate up to four drafts; if the fourth draft is still not approved, the workflow ends anyway. The printed heading says “FINAL APPROVED LESSON” even when the final draft may not have passed the rubric.

## Requirements

- Python 3.10 or newer
- An OpenRouter API key
- Access to the model configured in `Assessment.py` (`baidu/ernie-5.5-flash-preview:free`) through your OpenRouter account

Python packages are listed in `requirements.txt`:

- `langchain-core` for messages and shared LangChain types
- `langchain-openai` for the OpenAI-compatible chat client
- `langgraph` for defining and running the state graph

## Setup

Commands below assume the repository layout is:

```text
assessment/
├── .venv/                 # Python virtual environment (created below)
└── scaler/
    ├── Assessment.py
    ├── README.md
    └── requirements.txt
```

From the project root (`assessment`), create a virtual environment and install the requirements:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r scaler/requirements.txt
```

Confirm that the interpreter and package imports come from the virtual environment:

```bash
which python
python -c "import langchain_core, langchain_openai, langgraph; print('Dependencies are installed')"
```

The `which python` output should point to `assessment/.venv/bin/python`.

> **If your virtual environment already exists:** use its interpreter explicitly, for example `./.venv/bin/python -m pip install -r scaler/requirements.txt` from the project root. If the environment was moved from another folder, its activation scripts may still reference the old path. Recreate it in its current location, or continue to invoke its Python executable directly.

## Configure OpenRouter

The application reads `OPENROUTER_API_KEY` and `OPENROUTER_BASE_URL` from the process environment. Set them in the same terminal where you run the script:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
```

Keep the API key private. Do not commit it to source control or paste it into the README. The model name is set in `Assessment.py`; change it there if you want to use another model available to your OpenRouter account.

## Run

With the virtual environment activated, run from the project root:

```bash
python scaler/Assessment.py
```

Or, without activating the virtual environment:

```bash
.venv/bin/python scaler/Assessment.py
```

If you are already in the `scaler` directory, the equivalent commands are:

```bash
../.venv/bin/python Assessment.py
```

The run makes multiple model requests: one to generate each draft and one to evaluate it. The number of requests depends on how quickly the evaluator approves the lesson; the workflow may stop at the four-draft limit.

## Customize the lesson

To change the subject or audience, edit the `initial_state` dictionary near the bottom of `Assessment.py`:

```python
initial_state = {
    "topic": "RAG (Retrieval-Augmented Generation)",
    "target_audience": "12th-grade graduate in India with non-English medium background starting an AI career",
    "draft": "",
    "evaluation_feedback": "",
    "passed": False,
    "iteration_count": 0
}
```

Set a new value for `topic` and describe the intended reader in `target_audience`. The remaining fields initialize the graph and should normally start empty or false, with `iteration_count` set to zero.

You can also customize the prompts inside `generate_node` and `evaluate_node`, the evaluator rubric, the special first-review instruction, or the retry condition in `should_continue`.

## Troubleshooting

### `ModuleNotFoundError: No module named 'langchain_core'`

The script is being run with a Python interpreter that does not have the project dependencies installed. Activate the environment and install the requirements, or use that environment's Python explicitly:

```bash
source .venv/bin/activate
python -m pip install -r scaler/requirements.txt
python scaler/Assessment.py
```

Check `which python` before running. A prompt that visually shows an environment name does not guarantee that the shell resolved `python` or `pip` to that environment.

### `can't open file .../scaler.py`

The script's filename is `Assessment.py` (capital `A`) and it is inside the `scaler` directory. From the project root, run:

```bash
python scaler/Assessment.py
```

### OpenRouter authentication or model errors

Check that `OPENROUTER_API_KEY` is set in the current terminal and that the key is valid. Confirm that the model identifier in `Assessment.py` is available to your account and that `OPENROUTER_BASE_URL` is set to `https://openrouter.ai/api/v1`.
