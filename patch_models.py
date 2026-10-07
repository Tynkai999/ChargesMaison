import re

with open("core/models.py", "r") as f:
    content = f.read()

# Add import uuid
if "import uuid" not in content:
    content = "import uuid\n" + content

# For each class inheriting from models.Model, add the id field
def add_uuid_field(match):
    class_def = match.group(0)
    # Check if we already have it
    if "id = models.UUIDField" in class_def:
        return class_def
    
    # Insert right after the docstring or class definition
    lines = class_def.split("\n")
    insert_idx = 1
    for i, line in enumerate(lines):
        if '"""' in line:
            # If docstring is multi-line, find the end
            if line.count('"""') == 1:
                for j in range(i+1, len(lines)):
                    if '"""' in lines[j]:
                        insert_idx = j + 1
                        break
            else:
                insert_idx = i + 1
            break
            
    lines.insert(insert_idx, "    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)")
    return "\n".join(lines)

new_content = re.sub(r'class \w+\(models\.Model\):(?:\n\s+""".*?""")?', add_uuid_field, content, flags=re.DOTALL)

with open("core/models.py", "w") as f:
    f.write(new_content)
print("models.py patched with UUID fields.")
