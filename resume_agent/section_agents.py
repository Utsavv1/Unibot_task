"""
One specialist agent per resume section — each owns only its own tools, is
told to make the smallest possible edit, and must always act through a tool
rather than describing JSON. These are leaf agents; the Resume sub-agent
routes to exactly one of them.
"""

from google.adk.agents import LlmAgent

from resume_agent import tools

MODEL = "gemini-3.6-flash"

# kept this as one shared block so tone/rules stay consistent across all five agents
COMMON_RULES = """
STRICT RULES (apply to every action):
- You edit ONLY your own section. Never touch other sections.
- Every change MUST go through a tool call. NEVER output raw JSON and never
  claim an edit happened without calling a tool.
- Make the MINIMAL edit that satisfies the request. Do not rewrite or
  "improve" content the user did not ask you to change.
- If a request needs new wording (e.g. "make it more senior", "improve for
  impact"), YOU write the improved text, then pass it to the tool. Keep it
  truthful — never invent facts, employers, dates, or metrics that aren't
  implied by existing content.
- If you cannot identify which item the user means, call get_section first to
  look, and if still unclear, ask one short clarifying question instead of
  guessing.
- After a successful tool call, reply in one or two sentences describing what
  changed. Do not dump the whole resume.
"""


summary_agent = LlmAgent(
    name="summary_agent",
    model=MODEL,
    description="Reads and rewrites the resume summary / professional profile.",
    instruction=f"""You manage the resume SUMMARY only.

You handle requests like: rewrite the summary, make it more senior, tailor it
for leadership roles, shorten it, make it more concise, change the tone.

How to work:
1. If you need the current summary, call get_section("summary").
2. Compose the new summary text yourself, honoring the user's intent
   (seniority, length, focus). Keep it grounded in the existing summary — do
   not fabricate experience.
3. Save it with update_summary(text).

{COMMON_RULES}""",
    tools=[tools.get_section, tools.update_summary],
    disallow_transfer_to_peers=True,
)


experiences_agent = LlmAgent(
    name="experiences_agent",
    model=MODEL,
    description="Adds/edits/removes work experiences and their bullet points.",
    instruction=f"""You manage the EXPERIENCES section only.

You handle: adding/editing/removing bullets, rewriting bullets for impact,
updating role/organization/location/dates, and adding or removing whole jobs.

Reference resolution:
- "first job" -> ref="first", "second" -> "second", "last" -> "last".
- You may also use the experience id (e.g. "exp1") or a number ("1").
- Bullets are 0-based: the first bullet is bullet_index 0.

How to work:
1. Call get_section("experiences") when you need to see current content,
   especially before editing or removing a specific bullet.
2. For "improve bullets for impact": rewrite using strong action verbs and
   quantify ONLY with metrics already present or clearly implied. Then update
   each bullet with update_experience_bullet. Do not invent numbers.
3. Use the narrowest tool: add_experience_bullet, update_experience_bullet,
   remove_experience_bullet, update_experience, add_experience,
   remove_experience.

{COMMON_RULES}""",
    tools=[
        tools.get_section,
        tools.update_experience,
        tools.add_experience_bullet,
        tools.update_experience_bullet,
        tools.remove_experience_bullet,
        tools.add_experience,
        tools.remove_experience,
    ],
    disallow_transfer_to_peers=True,
)


educations_agent = LlmAgent(
    name="educations_agent",
    model=MODEL,
    description="Adds/edits/removes education entries.",
    instruction=f"""You manage the EDUCATIONS section only.

You handle: updating degree/institution/location/dates/details, and adding or
removing education entries.

Reference resolution: "first"/"last"/number, or an id like "edu1".

How to work:
1. Call get_section("educations") if you need to see current entries.
2. Use update_education for edits, add_education / remove_education otherwise.
   Pass only the fields the user asked to change.

{COMMON_RULES}""",
    tools=[
        tools.get_section,
        tools.update_education,
        tools.add_education,
        tools.remove_education,
    ],
    disallow_transfer_to_peers=True,
)


skills_agent = LlmAgent(
    name="skills_agent",
    model=MODEL,
    description="Adds/removes skills and changes their category.",
    instruction=f"""You manage the SKILLS section only.

You handle: adding a skill, removing a skill, and changing a skill's category
(e.g. Languages, Frameworks, Databases, Tools, Other).

How to work:
- Add: add_skill(name, category). Infer a sensible category if the user gives
  one or if it is obvious (e.g. "Python" -> "Languages"); otherwise "Other".
- Remove: remove_skill(ref) where ref can be the skill name (e.g. "React"),
  its id, or a number.
- Recategorize: update_skill_category(ref, category).
- If asked to add several skills, call add_skill once per skill.

{COMMON_RULES}""",
    tools=[
        tools.get_section,
        tools.add_skill,
        tools.remove_skill,
        tools.update_skill_category,
    ],
    disallow_transfer_to_peers=True,
)


projects_agent = LlmAgent(
    name="projects_agent",
    model=MODEL,
    description="Adds/edits/removes projects and their descriptions.",
    instruction=f"""You manage the PROJECTS section only.

You handle: editing a project's name/description/technologies/link, adding a
new project, and removing a project.

Reference resolution: "first"/"second"/"last"/number, an id like "proj1", or
the project name.

How to work:
1. Call get_section("projects") if you need to see current projects.
2. For "add a project about X": create a concise, truthful name and 1-2
   sentence description with update via add_project. Include obvious
   technologies if implied (e.g. "AI chatbot" -> ["Python"]) but keep it
   modest.
3. Use update_project for edits (pass only changed fields), remove_project to
   delete.

{COMMON_RULES}""",
    tools=[
        tools.get_section,
        tools.update_project,
        tools.add_project,
        tools.remove_project,
    ],
    disallow_transfer_to_peers=True,
)


SECTION_AGENTS = [
    summary_agent,
    experiences_agent,
    educations_agent,
    skills_agent,
    projects_agent,
]
