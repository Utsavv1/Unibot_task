"""
Every resume edit goes through one of these functions — agents never write
raw JSON, they call a tool and it does a small, schema-safe mutation on the
in-memory resume. Each one returns {status, message, ...} so the agent has
something to report back.

"ref" args accept an id ("exp2"), an ordinal ("first"/"last"), or a 1-based
number ("2") — covers phrasing like "my first job". Bad refs come back as
status="error" instead of raising, so nothing corrupts the resume.
"""

from typing import Optional, List
from resume_agent.resume_store import get_state, next_id, resolve_index


# =========================================================================
# READ TOOLS
# =========================================================================
def get_resume() -> dict:
    """Return the full resume JSON. Use this to inspect current content."""
    return {"status": "ok", "resume": get_state()}


def get_section(section_name: str) -> dict:
    """One section of the resume (summary/experiences/educations/skills/projects/basics)."""
    state = get_state()
    key = section_name.strip().lower()
    if key not in state:
        return {"status": "error",
                "message": f"Unknown section '{section_name}'. "
                           f"Valid: {list(state.keys())}"}
    return {"status": "ok", "section": key, "data": state[key]}


# =========================================================================
# SUMMARY TOOLS
# =========================================================================
def update_summary(text: str) -> dict:
    state = get_state()
    old = state.get("summary", "")
    state["summary"] = text.strip()
    return {"status": "ok",
            "message": "Summary updated.",
            "old": old,
            "new": state["summary"]}


# =========================================================================
# EXPERIENCE TOOLS
# =========================================================================
def update_experience(ref: str,
                      role: Optional[str] = None,
                      organization: Optional[str] = None,
                      location: Optional[str] = None,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None) -> dict:
    """Update one experience (by id/ordinal/number); only passed fields change."""
    exps = get_state()["experiences"]
    idx, exp = resolve_index(exps, ref)
    if exp is None:
        return {"status": "error", "message": f"No experience matches '{ref}'."}

    changed = {}
    for field, value in [("role", role), ("organization", organization),
                         ("location", location), ("start_date", start_date),
                         ("end_date", end_date)]:
        if value is not None:
            exp[field] = value
            changed[field] = value
    if not changed:
        return {"status": "error", "message": "No fields provided to update."}
    return {"status": "ok",
            "message": f"Updated experience '{exp['id']}'.",
            "changed": changed}


def add_experience_bullet(ref: str, bullet: str,
                          position: Optional[int] = None) -> dict:
    """
    Add a bullet to an experience. position is an optional 0-based index;
    if omitted the bullet is appended to the end.
    """
    exps = get_state()["experiences"]
    idx, exp = resolve_index(exps, ref)
    if exp is None:
        return {"status": "error", "message": f"No experience matches '{ref}'."}
    exp.setdefault("bullets", [])
    if position is None or position >= len(exp["bullets"]):
        exp["bullets"].append(bullet.strip())
    else:
        exp["bullets"].insert(max(0, position), bullet.strip())
    return {"status": "ok",
            "message": f"Added bullet to experience '{exp['id']}'.",
            "bullets": exp["bullets"]}


def update_experience_bullet(ref: str, bullet_index: int, new_text: str) -> dict:
    """bullet_index is 0-based."""
    exps = get_state()["experiences"]
    idx, exp = resolve_index(exps, ref)
    if exp is None:
        return {"status": "error", "message": f"No experience matches '{ref}'."}
    bullets = exp.get("bullets", [])
    if not (0 <= bullet_index < len(bullets)):
        return {"status": "error",
                "message": f"bullet_index {bullet_index} out of range "
                           f"(0..{len(bullets) - 1})."}
    old = bullets[bullet_index]
    bullets[bullet_index] = new_text.strip()
    return {"status": "ok",
            "message": f"Updated bullet {bullet_index} on '{exp['id']}'.",
            "old": old, "new": bullets[bullet_index]}


def remove_experience_bullet(ref: str, bullet_index: int) -> dict:
    exps = get_state()["experiences"]
    idx, exp = resolve_index(exps, ref)
    if exp is None:
        return {"status": "error", "message": f"No experience matches '{ref}'."}
    bullets = exp.get("bullets", [])
    if not (0 <= bullet_index < len(bullets)):
        return {"status": "error",
                "message": f"bullet_index {bullet_index} out of range."}
    removed = bullets.pop(bullet_index)
    return {"status": "ok",
            "message": f"Removed bullet from '{exp['id']}'.",
            "removed": removed}


def add_experience(role: str, organization: str,
                   start_date: str = "", end_date: str = "",
                   location: str = "", bullets: Optional[List[str]] = None) -> dict:
    exps = get_state()["experiences"]
    new = {
        "id": next_id("exp", exps),
        "role": role,
        "organization": organization,
        "location": location,
        "start_date": start_date,
        "end_date": end_date,
        "bullets": bullets or [],
    }
    exps.append(new)
    return {"status": "ok", "message": "Experience added.", "experience": new}


def remove_experience(ref: str) -> dict:
    """Remove an entire experience entry (by id, ordinal, or number)."""
    exps = get_state()["experiences"]
    idx, exp = resolve_index(exps, ref)
    if exp is None:
        return {"status": "error", "message": f"No experience matches '{ref}'."}
    removed = exps.pop(idx)
    return {"status": "ok", "message": "Experience removed.",
            "removed_id": removed["id"]}


# =========================================================================
# EDUCATION TOOLS
# =========================================================================
def update_education(ref: str,
                     degree: Optional[str] = None,
                     institution: Optional[str] = None,
                     location: Optional[str] = None,
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None,
                     details: Optional[str] = None) -> dict:
    """Only passed fields change."""
    edus = get_state()["educations"]
    idx, edu = resolve_index(edus, ref)
    if edu is None:
        return {"status": "error", "message": f"No education matches '{ref}'."}
    changed = {}
    for field, value in [("degree", degree), ("institution", institution),
                         ("location", location), ("start_date", start_date),
                         ("end_date", end_date), ("details", details)]:
        if value is not None:
            edu[field] = value
            changed[field] = value
    if not changed:
        return {"status": "error", "message": "No fields provided to update."}
    return {"status": "ok", "message": f"Updated education '{edu['id']}'.",
            "changed": changed}


def add_education(degree: str, institution: str,
                  start_date: str = "", end_date: str = "",
                  location: str = "", details: str = "") -> dict:
    edus = get_state()["educations"]
    new = {
        "id": next_id("edu", edus),
        "degree": degree, "institution": institution,
        "location": location, "start_date": start_date,
        "end_date": end_date, "details": details,
    }
    edus.append(new)
    return {"status": "ok", "message": "Education added.", "education": new}


def remove_education(ref: str) -> dict:
    """Remove an education entry (by id, ordinal, or number)."""
    edus = get_state()["educations"]
    idx, edu = resolve_index(edus, ref)
    if edu is None:
        return {"status": "error", "message": f"No education matches '{ref}'."}
    removed = edus.pop(idx)
    return {"status": "ok", "message": "Education removed.",
            "removed_id": removed["id"]}


# =========================================================================
# SKILLS TOOLS
# =========================================================================
def add_skill(name: str, category: str = "Other") -> dict:
    """Add a skill with an optional category (e.g. Languages, Frameworks)."""
    skills = get_state()["skills"]
    for s in skills:
        if s["name"].strip().lower() == name.strip().lower():
            return {"status": "error",
                    "message": f"Skill '{name}' already exists."}
    new = {"id": next_id("skill", skills),
           "name": name.strip(), "category": category.strip()}
    skills.append(new)
    return {"status": "ok", "message": "Skill added.", "skill": new}


def remove_skill(ref: str) -> dict:
    """Remove a skill by id, number, or name (e.g. "Python")."""
    skills = get_state()["skills"]
    idx, skill = resolve_index(skills, ref)
    # NOTE: falls back to a case-insensitive name match if ref isn't an id/ordinal/number
    # TODO: this fallback is duplicated in update_skill_category/remove_project below —
    # could factor out if a third section needs the same lookup
    if skill is None:
        for i, s in enumerate(skills):
            if s["name"].strip().lower() == str(ref).strip().lower():
                idx, skill = i, s
                break
    if skill is None:
        return {"status": "error", "message": f"No skill matches '{ref}'."}
    removed = skills.pop(idx)
    return {"status": "ok", "message": "Skill removed.", "removed": removed}


def update_skill_category(ref: str, category: str) -> dict:
    """By id, number, or name."""
    skills = get_state()["skills"]
    idx, skill = resolve_index(skills, ref)
    if skill is None:
        for i, s in enumerate(skills):
            if s["name"].strip().lower() == str(ref).strip().lower():
                idx, skill = i, s
                break
    if skill is None:
        return {"status": "error", "message": f"No skill matches '{ref}'."}
    skill["category"] = category.strip()
    return {"status": "ok",
            "message": f"Skill '{skill['name']}' moved to '{category}'.",
            "skill": skill}


# =========================================================================
# PROJECT TOOLS
# =========================================================================
def update_project(ref: str,
                   name: Optional[str] = None,
                   description: Optional[str] = None,
                   technologies: Optional[List[str]] = None,
                   link: Optional[str] = None) -> dict:
    """Only passed fields change."""
    projs = get_state()["projects"]
    idx, proj = resolve_index(projs, ref)
    if proj is None:
        return {"status": "error", "message": f"No project matches '{ref}'."}
    changed = {}
    for field, value in [("name", name), ("description", description),
                         ("technologies", technologies), ("link", link)]:
        if value is not None:
            proj[field] = value
            changed[field] = value
    if not changed:
        return {"status": "error", "message": "No fields provided to update."}
    return {"status": "ok", "message": f"Updated project '{proj['id']}'.",
            "changed": changed}


def add_project(name: str, description: str = "",
                technologies: Optional[List[str]] = None,
                link: str = "") -> dict:
    projs = get_state()["projects"]
    new = {
        "id": next_id("proj", projs),
        "name": name, "description": description,
        "technologies": technologies or [], "link": link,
    }
    projs.append(new)
    return {"status": "ok", "message": "Project added.", "project": new}


def remove_project(ref: str) -> dict:
    """Remove a project (by id, ordinal, number, or name)."""
    projs = get_state()["projects"]
    idx, proj = resolve_index(projs, ref)
    if proj is None:
        for i, p in enumerate(projs):
            if p["name"].strip().lower() == str(ref).strip().lower():
                idx, proj = i, p
                break
    if proj is None:
        return {"status": "error", "message": f"No project matches '{ref}'."}
    removed = projs.pop(idx)
    return {"status": "ok", "message": "Project removed.",
            "removed_id": removed["id"]}
