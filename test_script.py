with open("apps/website/src/styles/global.css", "r") as f:
    content = f.read()
if "focus-visible" not in content:
    print("focus-visible missing from global.css")
