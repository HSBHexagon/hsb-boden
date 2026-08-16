import re

with open('src/components/forms/LeadForm.astro', 'r') as f:
    content = f.read()

# Make sure all inputs, selects and textareas have the focus-visible styles.
def replace_class(m):
    original_class = m.group(1)
    if 'focus-visible' not in original_class:
        new_class = original_class + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red'
        return f'class="{new_class}"'
    return m.group(0)

content = re.sub(r'class="([^"]*rounded border border-hsb-line[^"]*)"', replace_class, content)

with open('src/components/forms/LeadForm.astro', 'w') as f:
    f.write(content)
