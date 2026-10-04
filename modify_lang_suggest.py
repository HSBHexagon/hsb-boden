import os

file_path = "apps/website/src/components/layout/LanguageSuggest.astro"
with open(file_path, "r") as f:
    content = f.read()

content = content.replace(
    '<a id="lang-suggest-link" class="button-primary !px-3 !py-1.5 text-xs" href="/en/"></a>',
    '<a id="lang-suggest-link" class="button-primary !px-3 !py-1.5 text-xs focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:ring-offset-2" href="/en/"></a>'
)

content = content.replace(
    '<button id="lang-suggest-dismiss" class="text-xs font-bold text-hsb-steel underline hover:text-hsb-black"></button>',
    '<button id="lang-suggest-dismiss" class="rounded text-xs font-bold text-hsb-steel underline hover:text-hsb-black focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-hsb-red focus-visible:ring-offset-2"></button>'
)

with open(file_path, "w") as f:
    f.write(content)
