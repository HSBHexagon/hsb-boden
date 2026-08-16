import re

with open('worker-configuration.d.ts', 'r') as f:
    content = f.read()

# Replace the specific todo line
old_line = "     *    - color: rgb or hex representation of the color you wish to trim (todo: verify the rgba bit)"
new_line = "     *    - color: rgb, rgba or hex representation of the color you wish to trim"

if old_line in content:
    content = content.replace(old_line, new_line)
    with open('worker-configuration.d.ts', 'w') as f:
        f.write(content)
    print("Updated successfully.")
else:
    print("Could not find the target line.")
