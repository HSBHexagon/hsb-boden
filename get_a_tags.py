import re
import os

for root, _, files in os.walk("apps/website/src/components"):
    for file in files:
        if file.endswith(".astro"):
            filepath = os.path.join(root, file)
            with open(filepath, "r") as f:
                content = f.read()
                matches = re.finditer(r'<a[^>]*class="[^"]*button-[^"]*"[^>]*>', content)
                for match in matches:
                    a_tag = match.group(0)
                    if 'focus-visible' not in a_tag:
                        print(f"{filepath}:\n{a_tag}\n")
