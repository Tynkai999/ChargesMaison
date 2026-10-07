import re

with open("core/views.py", "r") as f:
    content = f.read()

def replace_presence(match):
    return """
    presence_rows = [
        {"resident": r, "present": presence_map.get(r.id, True)} for r in residents
    ]
    
    if not request.user.is_staff:
        own_resident = getattr(request.user, "resident", None)
        if own_resident:
            my_presence = next((r for r in presence_rows if r["resident"].id == own_resident.id), None)
            if my_presence and not my_presence["present"]:
                presence_rows = [my_presence]
"""

content = re.sub(
    r'presence_rows = \[\n\s+\{"resident": r, "present": presence_map\.get\(r\.id, True\)\} for r in residents\n\s+\]',
    replace_presence,
    content
)

with open("core/views.py", "w") as f:
    f.write(content)
print("period_detail presence patched.")
