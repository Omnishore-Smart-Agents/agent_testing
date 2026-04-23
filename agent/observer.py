from tools.llm import detect_page_info


class Observer:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def observe(self, url: str) -> dict:
        print(f"👁️ [OBSERVE] Navigating to {url}")
        await self.browser.open_page(url)
        await self.browser.dismiss_cookies()

        fields = await self.browser.extract_inputs()
        lang, direction = await self.browser.detect_language()
        form_type = await self.browser.detect_form_type()
        page_text = await self.browser.get_page_text()

        page_info = detect_page_info(url, page_text)
        lang = page_info.get("language", lang)
        direction = page_info.get("direction", direction)
        form_type = page_info.get("form_type", form_type)

        signup_url_hint = page_info.get("signup_url_hint")
        if not signup_url_hint:
            signup_url_hint = self._find_signup_url(page_text, url)

        print(f"👁️ [OBSERVE] Language: {lang} ({direction}) | Form type: {form_type}")
        print(f"👁️ [OBSERVE] Detected {len(fields)} fields")

        return {
            "fields": fields,
            "language": lang,
            "direction": direction,
            "form_type": form_type,
            "labels": page_info.get("labels", {}),
            "submit_buttons": page_info.get("submit_buttons", []),
            "page_title": page_info.get("page_title", ""),
            "signup_url_hint": signup_url_hint,
        }

    def _find_signup_url(self, page_text: str, base_url: str) -> str | None:
        import re
        text_lower = page_text.lower()
        signup_patterns = [
            r'href=["\']([^"\']*(?:sign|register|signup|create.account|inscription|registrarse|registrieren|registro)[^"\']*)["\']',
            r'href=["\']([^"\']*/(?:sign-up|register|signup|create-account|inscription)[^"\']*)["\']',
        ]
        for pattern in signup_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if match.startswith("http"):
                    return match
                if match.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    return f"{parsed.scheme}://{parsed.netloc}{match}"
        return None