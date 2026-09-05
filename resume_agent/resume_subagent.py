"""
resume_subagent.py
-------------------
The Resume sub-agent sits between Unibot and the five section specialists.

Its ONLY job is to look at a resume-editing request, decide which section it
targets, and transfer control to the matching section agent. It does not edit
anything itself.
"""

from google.adk.agents import LlmAgent

from resume_agent import tools
from resume_agent.section_agents import SECTION_AGENTS

MODEL = "gemini-3.6-flash"

resume_agent = LlmAgent(
    name="resume_agent",
    model=MODEL,
    description=(
        "Owns the full resume. Figures out which resume section a request "
        "targets and routes it to the correct section specialist."
    ),
    instruction="""You are the Resume manager. You coordinate edits to a
resume that has these sections, each handled by a dedicated specialist:

- summary_agent      -> the professional summary / profile paragraph
- experiences_agent  -> work history, job bullets, roles, dates
- educations_agent   -> degrees, schools, education entries
- skills_agent       -> skills list and skill categories
- projects_agent     -> projects and their descriptions

YOUR JOB IS ROUTING, NOT EDITING:
- Read the user's request, identify the target section, and transfer to that
  one specialist. Transfer to exactly ONE agent.
- You may call get_resume() or get_section() only to disambiguate which
  section is meant. You must NOT perform edits yourself.

Routing cues:
- "summary", "profile", "make me sound senior/leadership", "shorten intro"
      -> summary_agent
- "job", "role", "experience", "bullet", "position", "employer", dates on a
  job -> experiences_agent
- "degree", "school", "university", "education", "GPA" -> educations_agent
- "skill", "add/remove <technology> to skills", "category" -> skills_agent
- "project", "portfolio piece", "add a project about ..." -> projects_agent

If a request spans two sections, handle the section the user named first and
briefly mention the other can be done next. If it is genuinely unclear which
section, ask one short clarifying question.""",
    tools=[tools.get_resume, tools.get_section],
    sub_agents=SECTION_AGENTS,
)
