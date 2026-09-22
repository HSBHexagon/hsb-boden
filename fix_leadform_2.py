with open("apps/website/src/components/forms/LeadForm.astro", "r") as f:
    content = f.read()

# Let's see the current script part
import re
print(re.search(r'const originalBtnText.*', content).group(0))
