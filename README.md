# Unibot + Resume Agents (Google ADK)

A small multi-agent system, built on the **Google Agent Development Kit (ADK)**,
that edits a resume (stored as JSON) from natural-language requests. Instead of
letting an LLM rewrite the resume as free text, every change is applied through
**tools (functions)** so the JSON always stays schema-valid.

---

## Agent Hierarchy

```
Unibot (root)                  greets, answers general questions, detects resume intent
   └── Resume Sub-Agent        owns the full resume, routes to the right section
         ├── Summary Agent     rewrites / shortens / retones the summary
         ├── Experiences Agent add/edit/remove jobs and bullets, update role/dates
         ├── Educations Agent  edit/add/remove education entries
         ├── Skills Agent      add/remove skills, change category
         └── Projects Agent    edit/add/remove projects and descriptions
```

**How a request flows** — e.g. *"Add a leadership bullet to my first experience"*:
1. **Unibot** recognizes a resume edit -> transfers to the Resume sub-agent.
2. **Resume sub-agent** sees it targets work history -> transfers to the Experiences agent.
3. **Experiences agent** writes a leadership-style bullet and calls
   `add_experience_bullet("first", "<bullet>")`.
4. The tool mutates only that experience. Nothing else changes.

Each agent has a **narrow responsibility**, which keeps its prompt tight and
prevents it from touching unrelated sections. ADK handles the actual
parent -> sub_agent delegation (LLM-driven transfer), so routing lives in the prompts.

---

## How to Run

Requires **Python 3.10+** and a **Gemini API key** (ADK uses Gemini by default).

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your API key
cp resume_agent/.env.example resume_agent/.env
#   then edit resume_agent/.env and set GOOGLE_API_KEY=...
#   (get a free key at https://aistudio.google.com/apikey)

# 3a. Launch the web chat UI (recommended)
adk web
#     then open the printed URL and pick the "resume_agent" app

# 3b. ...or run in the terminal
adk run resume_agent
```

> Run `adk web` / `adk run` from the **project root** (this folder). ADK
> discovers the `resume_agent` package, which exposes `root_agent`.

---

## How to Change the Resume

The resume lives in **one file**:

> **To use a different resume, edit `resume_agent/resume.json`.**

It is loaded once at startup. Replace its contents with any resume that follows
the schema below and restart the agent — no code changes needed.

### Resume JSON Schema

```jsonc
{
  "basics":   { "name", "title", "email", "phone", "location" },
  "summary":  "string",
  "experiences": [
    { "id", "role", "organization", "location",
      "start_date", "end_date", "bullets": ["string", ...] }
  ],
  "educations": [
    { "id", "degree", "institution", "location",
      "start_date", "end_date", "details" }
  ],
  "skills": [
    { "id", "name", "category" }
  ],
  "projects": [
    { "id", "name", "description", "technologies": ["string", ...], "link" }
  ]
}
```

Every list item carries a stable `id` (e.g. `exp1`, `skill3`). Tools also accept
ordinals (`"first"`, `"last"`), 1-based numbers (`"2"`), and — for skills and
projects — the item's name, so phrasing like *"my first job"* or *"remove
React"* works.

---

## Tools (Functions)

All edits go through these; agents never emit raw JSON.

| Tool | Purpose |
|------|---------|
| `get_resume()` | Return the full resume JSON |
| `get_section(section_name)` | Return one section |
| `update_summary(text)` | Replace the summary |
| `update_experience(ref, ...)` | Update role/org/location/dates on a job |
| `add_experience_bullet(ref, bullet, position?)` | Add a bullet to a job |
| `update_experience_bullet(ref, bullet_index, new_text)` | Rewrite one bullet |
| `remove_experience_bullet(ref, bullet_index)` | Delete one bullet |
| `add_experience(role, organization, ...)` | Add a whole job |
| `remove_experience(ref)` | Delete a job |
| `update_education(ref, ...)` | Update an education entry |
| `add_education(degree, institution, ...)` | Add an education entry |
| `remove_education(ref)` | Delete an education entry |
| `add_skill(name, category?)` | Add a skill (dedups by name) |
| `remove_skill(ref)` | Remove a skill (by name/id/number) |
| `update_skill_category(ref, category)` | Recategorize a skill |
| `update_project(ref, ...)` | Update a project's fields |
| `add_project(name, description, ...)` | Add a project |
| `remove_project(ref)` | Remove a project |

**Schema safety:** every tool validates its reference, changes only the fields
passed, generates non-colliding ids for new items, and returns
`{status, message, ...}` instead of raising — so a bad reference reports an
error rather than corrupting the resume.

---

## Sample Test Queries

```
Show me my resume
Make my summary more senior
Rewrite my summary for leadership roles
Shorten my summary
Add a leadership bullet to my first experience
Improve my first job bullets for impact
Update the role of my first job to "Staff Engineer"
Add Python to my skills            (already present -> reports it exists)
Add Docker to my skills
Remove React from my skills
Remove my second project
Add a project about an AI chatbot
```

---

## Prompt Design (short)

The prompts are built around four goals the task emphasizes:

- **Clear boundaries.** Each section agent is told it owns *only* its section
  and must never touch others. `disallow_transfer_to_peers=True` stops leaf
  agents from bouncing work sideways.
- **Force tool usage.** A shared rule block states that *every* change must go
  through a tool and the agent must never output raw JSON or claim an edit it
  didn't make via a tool.
- **Minimal, non-destructive edits.** Agents are instructed to make the
  smallest change that satisfies the request and to leave unrelated content
  alone. Update tools only modify the fields actually passed.
- **Intent handling without fabrication.** For fuzzy asks ("more senior",
  "improve for impact") the agent writes the new wording itself, but is told to
  stay truthful — no invented employers, dates, or metrics. Ambiguous
  references trigger a `get_section` look-up or one short clarifying question
  instead of a guess.

Routing is layered: **Unibot** only decides "resume or not," the **Resume
sub-agent** only decides "which section," and the **section agent** does the
actual tool call. This keeps each decision simple and each prompt short.

---

## Project Structure

```
unibot_resume/
├── README.md
├── requirements.txt
└── resume_agent/
    ├── __init__.py            exposes root_agent
    ├── agent.py               Unibot (root_agent)
    ├── resume_subagent.py     Resume routing sub-agent
    ├── section_agents.py      the 5 section specialists
    ├── tools.py               all read/modify tools
    ├── resume_store.py        single load point + reference resolution
    ├── resume.json            <-- the resume (edit this to swap)
    └── .env.example           copy to .env, add GOOGLE_API_KEY
```

---

## Out of Scope

No auth, database, frontend, deployment, or backend servers — by design. State
lives in memory, loaded from `resume.json`.
