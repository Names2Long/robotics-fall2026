from perception.experiments import validate, signature

QUESTIONS = {
    "mission_1": ("diagnosis", "limitations"),
    "mission_2": ("comparison", "choice"),
    "pillar_search": ("diagnosis", "evidence"),
    "line_following": ("comparison", "limits"),
}


def mission_ready(state, mission):
    evidence = state["evidence"].get(mission)
    try:
        if mission in ("mission_1", "mission_2"):
            validate(evidence, "classical" if mission == "mission_1" else "learned")
            if mission == "mission_1":
                # Earlier expression-based evidence remains readable. New runs
                # execute the supplied code with the student's saved parameters.
                if evidence.get("implementation"):
                    from perception.student_code import check_implementation
                    check_implementation(evidence["implementation"])
            if mission == "mission_2":
                validate(state["evidence"].get("mission_1"), "classical")
                if evidence.get("comparison_run") != signature(state["evidence"]["mission_1"]):
                    raise ValueError("Classical results changed. Review and save the comparison again")
                from perception.dataset import CONDITIONS
                conditions = evidence.get('comparison_conditions', [])
                if not isinstance(conditions, list) or len(set(conditions)) < 3 or any(c not in CONDITIONS for c in conditions):
                    raise ValueError('Select at least three conditions in Part C and save the comparison')
        elif mission in ('pillar_search','line_following'):
            from perception.robot_evidence import validate_bundle
            validate_bundle(evidence,mission)
        else:
            return False, 'This archived activity is not part of the current detector investigation'
        missing = [q for q in QUESTIONS[mission] if not str(state["responses"].get(f"{mission}.{q}", "")).strip()]
        if missing: return False, "Answer: " + ", ".join(missing)
        return True, "Ready"
    except (ValueError, TypeError, KeyError) as error:
        return False, str(error)


def readiness(state):
    labels = {'mission_1': 'Mission 1, Part A: classical detector', 'mission_2': 'Mission 1, Parts B and C: learned vision and comparison',
              'pillar_search':'Mission 2: live pillar search', 'line_following':'Mission 3: live line following'}
    rows = []
    for mission in QUESTIONS:
        ready, detail = mission_ready(state, mission)
        rows.append({'item': labels[mission], 'ready': ready, 'detail': detail})
    rows.append({"item": "identity", "ready": all(str(state["student"].get(k, "")).strip() for k in ("name", "email")), "detail": "Name and student ID or email"})
    rows.append({"item": "synthesis", "ready": bool(str(state["responses"].get("final.synthesis", "")).strip()), "detail": "Complete the technical synthesis"})
    count = len(str(state["responses"].get("final.course_reflection", "")).split())
    rows.append({"item": "reflection", "ready": 1 <= count <= 300, "detail": f"{count}/300 words"})
    return rows
