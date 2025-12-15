def normalize_plan(plan):

    if not isinstance(plan, dict):
        return {"mode": "CHAT", "response": str(plan)}

    if "tool" in plan:
        if plan["tool"] is None:
            return {"mode": "CHAT", "response": "Tôi không hiểu yêu cầu của bạn."}
        plan.setdefault("args", {})
        return {"mode": "TOOL", "tool": plan["tool"], "args": plan["args"]}

    for f in ["message", "response", "content", "text"]:
        if f in plan and isinstance(plan[f], str):
            return {"mode": "CHAT", "response": plan[f]}

    return {"mode": "CHAT", "response": str(plan)}
