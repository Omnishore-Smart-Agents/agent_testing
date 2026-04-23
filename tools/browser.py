import os
import asyncio
from playwright.async_api import async_playwright

class BrowserWrapper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    async def open_page(self, url: str):
        await self.page.goto(url, wait_until="networkidle", timeout=60000)

    async def extract_inputs(self):
        inputs = await self.page.query_selector_all("input")
        fields = []
        for inp in inputs:
            atype = await inp.get_attribute("type")
            aname = await inp.get_attribute("name")
            aid = await inp.get_attribute("id")
            aplaceholder = await inp.get_attribute("placeholder")
            if atype not in ["hidden", "submit", "button"]:
                fields.append({
                    "type": atype,
                    "name": aname,
                    "id": aid,
                    "placeholder": aplaceholder
                })
        return fields
    
    async def fill_field(self, field_identifier: str, value: str):
        # We try strict matches first
        selectors = [
            f"input[name='{field_identifier}']",
            f"input[id='{field_identifier}']",
            f"input[placeholder='{field_identifier}']",
            f"#{field_identifier}"
        ]
        
        filled = False
        for sel in selectors:
            try:
                elements = await self.page.locator(sel).count()
                if elements > 0:
                    await self.page.fill(sel, value, timeout=1000)
                    filled = True
                    break
            except Exception:
                continue
                
        if not filled:
            raise Exception(f"Could not find field for identifier '{field_identifier}'")

    async def click_submit(self):
        submit_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:has-text('Submit')",
            "button:has-text('Login')",
            "button:has-text('Sign In')",
            ".btn",
            "#submit"
        ]
        
        for sel in submit_selectors:
            try:
                elements = await self.page.locator(sel).count()
                if elements > 0:
                    await self.page.click(sel, timeout=1000)
                    return True
            except Exception:
                continue
                
        raise Exception("Submit button not found.")

    async def wait_for_load(self):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(1)
        
    async def take_screenshot(self, name: str):
        os.makedirs("output/screenshots", exist_ok=True)
        path = f"output/screenshots/{name}.png"
        await self.page.screenshot(path=path)
        return path

    async def get_page_content(self):
        return await self.page.content()

    async def get_page_url(self):
        return self.page.url

    async def has_error_message(self):
        # basic heuristic
        text = await self.page.locator("body").inner_text()
        text_lower = text.lower()
        if "invalid username" in text_lower or "incorrect username" in text_lower or "error" in text_lower or "invalid" in text_lower:
            return True
        return False

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
