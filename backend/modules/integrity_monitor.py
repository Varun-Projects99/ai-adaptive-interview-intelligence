
violations = {}

def check_violation(session_id, vtype):

    if session_id not in violations:
        violations[session_id] = 0

    violations[session_id] += 1

    count = violations[session_id]

    return {
        "count": count,
        "terminate": count >= 3
    }
