class Observer:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def observe(self, url: str):
        """
        Navigates to URL and extracts inputs.
        """
        print(f"👁️ [OBSERVE] Navigating to {url}")
        await self.browser.open_page(url)
        fields = await self.browser.extract_inputs()
        print(f"👁️ [OBSERVE] Detected {len(fields)} fields: {fields}")
        return fields
