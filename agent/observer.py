from tools.llm import detect_page_info

class Observer:
    """Observes the current page state and extracts information."""
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def observe(self, url: str) -> dict:
        print(f"🔍 [OBSERVER] Navigating to {url}")
        await self.browser.page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Extract fields
        fields = await self.browser.get_form_fields()
        
        # Get page text for context
        page_text = await self.browser.get_page_text()
        
        # Detect page info via LLM
        print(f"🔍 [OBSERVER] Analyzing page content with AI...")
        info = detect_page_info(url, page_text, fields)
        
        # Ensure fields are included in the result
        info["fields"] = fields
        return info
