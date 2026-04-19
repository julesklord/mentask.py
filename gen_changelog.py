import re
from collections import defaultdict

# Load history
with open("G:/DEVELOPMENT/askgem.py/git_history.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

changelog = []
current_version = "Unknown"
version_data = defaultdict(lambda: {"date": "", "changes": []})

# Regex to extract info
# Format: hash | date | message
pattern = re.compile(r"([a-f0-9]+) \| (\d{4}-\d{2}-\d{2}) \| (.*)")

for line in lines:
    match = pattern.match(line)
    if not match:
        continue
    
    commit_hash, date, message = match.groups()
    
    # Identify release commits
    release_match = re.match(r"release: v(\d+\.\d+\.\d+)", message)
    if release_match:
        current_version = release_match.group(1)
        version_data[current_version]["date"] = date
        continue
    
    # Categorize changes
    category = "Changed"
    if "feat:" in message or "feat" in message:
        category = "Added"
    elif "fix:" in message or "fix" in message:
        category = "Fixed"
    elif "refactor:" in message or "refactor" in message:
        category = "Changed"
    elif "docs:" in message or "docs" in message:
        category = "Changed"
    elif "chore:" in message or "chore" in message:
        category = "Changed"
    elif "sec:" in message or "security" in message:
        category = "Fixed"

    # Clean message
    clean_message = message.replace(f"{category.lower()}:", "").strip()
    version_data[current_version]["changes"].append(f"- {category}: {clean_message} ({commit_hash})")

# Generate Markdown
output = ["# Changelog\n\nAll notable changes to this project will be documented in this file.\n\n"]
# Add legendary names mapping (manual for now)
names = {"0.15.0": "Kwisatz Haderach", "0.14.0": "Stability Pulse", "0.13.0": "Muad'Dib", "0.12.0": "Bene Gesserit", "0.11.0": "Orchestra", "0.10.0": "The Modular Jump"}

for ver in sorted(version_data.keys(), reverse=True):
    name = f' - "{names[ver]}"' if ver in names else ""
    output.append(f"## [{ver}]{name} - {version_data[ver]['date']}\n")
    
    # Group by category
    categories = defaultdict(list)
    for change in version_data[ver]["changes"]:
        cat = change.split(":")[0].replace("- ", "")
        categories[cat].append(change)
        
    for cat, changes in categories.items():
        output.append(f"### {cat}\n")
        output.extend(changes)
        output.append("\n")

with open("G:/DEVELOPMENT/askgem.py/CHANGELOG_NEW.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output))
