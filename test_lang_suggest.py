from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(locale='en-US')
    page = context.new_page()
    page.goto('http://localhost:4321') # We need a dev server running first!
    print("Done")
