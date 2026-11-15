import os
from typing import TypedDict
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# 1. Define the State of the Graph
class LessonState(TypedDict):
    topic: str
    target_audience: str
    draft: str
    evaluation_feedback: str
    passed: bool
    iteration_count: int


llm = ChatOpenAI(
    model="baidu/ernie-5.5-flash-preview:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)

# 2. Generator Node 
def generate_node(state: LessonState):
    print(f"\n---  Generating lesson for topic: '{state['topic']}' (Attempt {state['iteration_count'] + 1}) ---")
    
    prompt = f"""
    You are an expert instructional designer and tech educator for beginners.
    Create a beginner-friendly lesson on the topic: '{state['topic']}'.
    
    Target Audience Constraints:
    - Audience: {state['target_audience']}
    - Language: Extremely simple English, short sentences, avoiding dense academic definitions.
    - Structure: Start with a real-related analogy, explain what it is, why it matters, and how it works step-by-step.
    """
    
    if state["evaluation_feedback"]:
        prompt += f"\n\nAddress this feedback from the previous evaluation:\n{state['evaluation_feedback']}"

    response = llm.invoke([HumanMessage(content=prompt)])
    # print("<-------- GENERATED ON FIRST TRY ------->")
    # print(response.content)

    return {
        "draft": response.content,
        "iteration_count": state["iteration_count"] + 1
    }

# 3. Evaluator Node (Dynamic Rubric Check based on state['topic'])
def evaluate_node(state: LessonState):
    print(f"\n--- [EVALUATOR] Judging lesson quality against rubric for topic: '{state['topic']}' ---")
    
    eval_prompt = f"""
    You are a strict curriculum quality judge. Evaluate the following lesson draft about '{state['topic']}' based on these 4 rubric rules:
    1. ACCURACY: Is the explanation of '{state['topic']}' technically correct and directly addressing the assigned topic?
    2. ANALOGY: Does it start with a clear, relatable real-world analogy?
    3. SIMPLICITY: Is the vocabulary simple enough for a 12th-grade graduate with limited English? No unexplained heavy jargon.
    4. STRUCTURE: Does it clearly explain what, why, and how?

    Lesson Draft:
    {state['draft']}

    Respond strictly in this format:
    PASSED: [True or False]
    FEEDBACK: [If False, provide precise, actionable bullet points on what needs to be fixed. If True, we "APPROVED"rit]
    """
    result_text = ""
    
    response = llm.invoke([HumanMessage(content=eval_prompt)])
    
    if state['iteration_count'] == 1:
        passed = False
        result_text = 'Too advanced english. make it simpler so that everyone can understand.'
    else:
        result_text = response.content
        passed = "PASSED: True" in result_text or "PASSED: TRUE" in result_text
    
    return {
        "evaluation_feedback": result_text,
        "passed": passed
    }

# 4. Conditional Edge Logic
def should_continue(state: LessonState):
    if state["passed"] or state["iteration_count"] > 3:
        return "end"
    return "regenerate"

# 5. Build the LangGraph Workflow
workflow = StateGraph(LessonState)

workflow.add_node("generator", generate_node)
workflow.add_node("evaluator", evaluate_node)

workflow.set_entry_point("generator")
workflow.add_edge("generator", "evaluator")

workflow.add_conditional_edges(
    "evaluator",
    should_continue,
    {
        "regenerate": "generator",
        "end": END
    }
)

app = workflow.compile()

# 6. Execute the Pipeline with Any Dynamic Topic
if __name__ == "__main__":
    initial_state = {
        "topic": "RAG (Retrieval-Augmented Generation)",
        "target_audience": "12th-grade graduate in India with non-English medium background starting an AI career",
        "draft": "",
        "evaluation_feedback": "",
        "passed": False,
        "iteration_count": 0
    }
    
    final_output = app.invoke(initial_state)
    
    print("\n=== FINAL APPROVED LESSON ===")
    print(final_output["draft"])
    print(f"\nCompleted in {final_output['iteration_count']} iterations.")
    print("\n=== FEEDBACK FRON EVALUATOR AGENT ===")
    print(final_output['evaluation_feedback'])