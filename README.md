# Agentic Lesson Generator

This project uses a LangGraph workflow with two LLM-powered agents to create and improve a beginner-friendly lesson for a specified topic and audience.

## Workflow

```text
Start
  |
  v
Generator --> Evaluator
                 |
          +------+------+
          |             |
       Approved     Not approved
          |             |
          v             v
         End        Generator
                       (revise)
```

The workflow repeats generation and evaluation until the lesson is approved or the generation limit is reached.

### 1. Generator

The generator creates a lesson using the topic and target audience in the workflow state. Its prompt asks for:

- A relatable real-world analogy
- Simple English and short sentences
- An explanation of what the topic is, why it matters, and how it works, step by step

If the evaluator previously returned feedback, the generator includes it in the next prompt and revises the lesson accordingly. Every new draft increments the iteration count.

### 2. Evaluator

The evaluator reviews the latest draft against four criteria:

1. **Accuracy:** Is the explanation technically correct and on topic?
2. **Analogy:** Does it begin with a clear, relatable analogy?
3. **Simplicity:** Is the language understandable for the intended audience?
4. **Structure:** Does it explain what, why, and how?

It returns a pass status and feedback. The workflow recognizes approval when the response contains `PASSED: True` or `PASSED: TRUE`; otherwise, it routes the feedback back to the generator.

### 3. Conditional routing and iteration limit

After each evaluation, the router checks the pass status and iteration count:

- If the evaluator approves the lesson, the workflow ends.
- If the lesson is not approved and fewer than four drafts have been generated, the workflow returns to the generator.
- If four drafts have been generated, the workflow ends even if the latest draft was not approved.

Each draft is evaluated before the routing decision. Therefore, a run can make up to four generation calls and four evaluation calls.

## State passed between agents

The graph shares these values between its nodes:

| State field | Role in the workflow |
|---|---|
| `topic` | The subject the lesson should teach. |
| `target_audience` | The intended reader, used to guide the lesson's language and examples. |
| `draft` | The latest lesson created by the generator. |
| `evaluation_feedback` | The latest evaluator response, used to guide a revision. |
| `passed` | Whether the evaluator approved the current draft. |
| `iteration_count` | How many lesson drafts have been generated. |

The initial state supplies the topic and audience, starts with an empty draft and feedback, sets `passed` to false, and sets the iteration count to zero. The example currently uses RAG (Retrieval-Augmented Generation) as its topic.

## Result

When the workflow finishes, the program prints the latest lesson, the number of drafts generated, and the latest evaluator feedback. If the iteration limit is reached before approval, the returned lesson is the latest draft, but it may not have passed the evaluator's rubric.
