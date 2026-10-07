import re

with open("core/views.py", "r") as f:
    content = f.read()

helper = """
def _filter_summary_for_user(summary, user):
    if user.is_staff:
        return summary
    own_resident = getattr(user, "resident", None)
    if not own_resident:
        return summary
    my_line = next((line for line in summary["lines"] if line["resident"].id == own_resident.id), None)
    if my_line and not my_line["present"]:
        summary["lines"] = [my_line]
    return summary
"""

content = content.replace("def _auto_close_past_periods():", helper + "\ndef _auto_close_past_periods():")

# dashboard
content = content.replace("summaries = [compute_period_summary(p) for p in periods]", "summaries = [_filter_summary_for_user(compute_period_summary(p), request.user) for p in periods]")

# period_detail
content = content.replace("summary = compute_period_summary(period)", "summary = _filter_summary_for_user(compute_period_summary(period), request.user)")

with open("core/views.py", "w") as f:
    f.write(content)
print("views.py patched.")
