import re

with open('src/components/forms/LeadForm.astro', 'r') as f:
    content = f.read()

def replace_class(m):
    original_class = m.group(1)
    if 'focus-visible' not in original_class:
        new_class = original_class + ' focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red'
        return f'class="{new_class}"'
    return m.group(0)

# Replace all classes for form fields
content = re.sub(r'class="([^"]*rounded border border-hsb-line[^"]*)"', replace_class, content)

# Checkboxes
content = content.replace('type="checkbox" name="loads" value={option} />', 'type="checkbox" name="loads" value={option} class="focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red" />')
content = content.replace('type="checkbox" name="privacyConsent" class="mt-1"', 'type="checkbox" name="privacyConsent" class="mt-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red"')

replacements = [
    (r"Vorname\n\s*<input", r"<span>Vorname <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <input"),
    (r"Nachname\n\s*<input", r"<span>Nachname <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <input"),
    (r"Firma\n\s*<input", r"<span>Firma <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n    <input"),
    (r"E-Mail\n\s*<input", r"<span>E-Mail <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <input"),
    (r"Telefon\n\s*<input", r"<span>Telefon <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <input"),
    (r"Branche\n\s*<select", r"<span>Branche <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <select"),
    (r"Projektart\n\s*<select", r"<span>Projektart <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <select"),
    (r"Laufender Betrieb\n\s*<select", r"<span>Laufender Betrieb <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n      <select"),
    (r"Nachricht\n\s*<textarea", r"<span>Nachricht <span class=\"text-hsb-red\" aria-hidden=\"true\">*</span></span>\n    <textarea"),
]

for search, replace in replacements:
    content = re.sub(search, replace, content)

content = content.replace('Belastungen <span class="font-normal text-hsb-steel">(mindestens eine auswählen)</span>', '<span>Belastungen <span class="font-normal text-hsb-steel">(mindestens eine auswählen)</span> <span class="text-hsb-red" aria-hidden="true">*</span></span>')
content = content.replace('Ich stimme zu, dass meine Angaben zur Bearbeitung der Anfrage verarbeitet werden.', '<span>Ich stimme zu, dass meine Angaben zur Bearbeitung der Anfrage verarbeitet werden. <span class="text-hsb-red" aria-hidden="true">*</span></span>')

# Clean up any potential over-escaping
content = content.replace('aria-hidden=\\"true\\"', 'aria-hidden="true"')

with open('src/components/forms/LeadForm.astro', 'w') as f:
    f.write(content)
