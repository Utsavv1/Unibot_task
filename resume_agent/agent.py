"""
agent.py
---------
Unibot — the root agent that `adk web` / `adk run` loads.

Unibot is the front door: it greets users, answers general career / Unimad
questions itself, and detects when a request is about editing the resume. When
it is, Unibot hands off to the Resume sub-agent, which routes to the right
section specialist.

ADK requires this module to expose a variable named `root_agent`.
"""

from google.adk.agents import LlmAgent

from resume_agent.resume_subagent import resume_agent
from resume_agent.resume_store import load_resume

# Load the resume once at import time so the state is ready before any request.
load_resume()

MODEL = "gemini-3.6-flash"

root_agent = LlmAgent(
    name="unibot",
    model=MODEL,
    description=(
        "Unibot: the Unimad assistant. Greets users, answers general career "
        "and product questions, and delegates resume-editing requests."
    ),
    instruction="""You are Unibot, the friendly assistant for Unimad.

WHAT YOU DO YOURSELF:
- Greet users warmly and briefly.
- Answer general questions about careers, resumes, job searching, and Unimad.

WHAT YOU DELEGATE:
- Any request to VIEW or EDIT the user's resume -> transfer to resume_agent.
  This includes summary rewrites, experience/bullet changes, education edits,
  skills additions/removals, and project changes.

Examples that should go to resume_agent:
- "Edit my summary" / "Make my summary more senior"
- "Add a bullet to my first job" / "Improve my first job bullets"
- "Add Python to my skills" / "Remove my second project"
- "Show me my resume" / "What's in my skills section?"

Rules:
- Do NOT try to edit the resume yourself and do NOT invent resume content —
  always transfer editing/viewing to resume_agent.
- For anything that is clearly not about the resume, answer directly and
  helpfully; keep general answers concise.
- If a message is ambiguous, ask a short clarifying question.""",
    sub_agents=[resume_agent],
)
