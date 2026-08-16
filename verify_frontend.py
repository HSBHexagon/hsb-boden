from playwright.sync_api import sync_playwright
import time

def verify_frontend():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:4321/kontakt/')
        # Accept cookies to avoid interception
        page.locator('#cookie-accept-all').click()
        time.sleep(1)
        # Tab to focus the first input field
        page.locator('input[name="firstName"]').focus()
        page.screenshot(path='/tmp/screenshot.png')
        browser.close()

verify_frontend()
