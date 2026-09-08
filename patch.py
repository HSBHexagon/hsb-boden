import re

with open("src/components/forms/LeadForm.astro", "r") as f:
    content = f.read()

# Add span and asterisk to labels with required inputs
# We need to target specific labels. Let's do it manually using replace.

replacements = [
    (
        '      Vorname\n      <input required minlength={2} maxlength={80} name="firstName" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '      <span>Vorname<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <input required minlength={2} maxlength={80} name="firstName" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '      Nachname\n      <input required minlength={2} maxlength={80} name="lastName" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '      <span>Nachname<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <input required minlength={2} maxlength={80} name="lastName" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '    Firma\n    <input required minlength={2} maxlength={120} name="company" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '    <span>Firma<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n    <input required minlength={2} maxlength={120} name="company" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '      E-Mail\n      <input required type="email" name="email" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '      <span>E-Mail<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <input required type="email" name="email" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '      Telefon\n      <input required minlength={5} type="tel" name="phone" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '      <span>Telefon<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <input required minlength={5} type="tel" name="phone" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '      Branche\n      <select required name="industry" class="rounded border border-hsb-line px-3 py-3 font-normal">',
        '      <span>Branche<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <select required name="industry" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none">'
    ),
    (
        '      Projektart\n      <select required name="projectType" class="rounded border border-hsb-line px-3 py-3 font-normal">',
        '      <span>Projektart<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <select required name="projectType" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none">'
    ),
    (
        '      Fläche in m²\n      <input name="areaSize" class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '      Fläche in m²\n      <input name="areaSize" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '      Laufender Betrieb\n      <select required name="liveOperation" class="rounded border border-hsb-line px-3 py-3 font-normal">',
        '      <span>Laufender Betrieb<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n      <select required name="liveOperation" class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none">'
    ),
    (
        '    Nachricht\n    <textarea required minlength={10} maxlength={2000} name="message" rows={5} class="rounded border border-hsb-line px-3 py-3 font-normal" />',
        '    <span>Nachricht<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span>\n    <textarea required minlength={10} maxlength={2000} name="message" rows={5} class="rounded border border-hsb-line px-3 py-3 font-normal focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none" />'
    ),
    (
        '<input type="checkbox" name="loads" value={option} />',
        '<input type="checkbox" name="loads" value={option} class="focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none focus-visible:ring-offset-1" />'
    ),
    (
        '<input required type="checkbox" name="privacyConsent" class="mt-1" />',
        '<input required type="checkbox" name="privacyConsent" class="mt-1 focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none focus-visible:ring-offset-1" />'
    ),
    (
        '    class="button-primary disabled:cursor-not-allowed disabled:opacity-60"',
        '    class="button-primary disabled:cursor-not-allowed disabled:opacity-60 focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:outline-none focus-visible:ring-offset-2"'
    ),
    (
        '<legend class="text-sm font-black">Belastungen <span class="font-normal text-hsb-steel">(mindestens eine auswählen)</span></legend>',
        '<legend class="text-sm font-black"><span>Belastungen<span class="text-hsb-red ml-1" aria-hidden="true">*</span></span> <span class="font-normal text-hsb-steel">(mindestens eine auswählen)</span></legend>'
    )
]

for old, new in replacements:
    content = content.replace(old, new)

with open("src/components/forms/LeadForm.astro", "w") as f:
    f.write(content)
