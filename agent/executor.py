import asyncio
import os

class Executor:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def fill_form(self, form_data: dict) -> dict:
        """
        Fill a form with the given data. form_data is {identifier: value}.
        Returns a dict of results: {identifier: 'ok' | 'failed'}.
        """
        results = {}
        for identifier, value in form_data.items():
            if not value:
                continue
            # Try as regular input first
            success = await self.browser.fill_field(identifier, str(value))
            if not success:
                # Try as select dropdown
                success = await self.browser.select_option(identifier, str(value))
            
            status = "ok" if success else "failed"
            results[identifier] = status
            symbol = "✅" if success else "❌"
            print(f"  {symbol} {identifier} = '{value}' -> {status}")
            await asyncio.sleep(0.3)

        return results

    async def click_submit(self, buttons: list) -> bool:
        """
        Try to click the submit/register button from a list of visible buttons.
        """
        submit_keywords = [
            "submit", "register", "sign up", "create", "join",
            "s'inscrire", "valider", "envoyer", "soumettre", "adhérer",
            "confirmer", "continuer", "continue", "next", "suivant",
            "se connecter", "log in", "login", "connexion", "je me connecte", "sign in"
        ]
        skip_keywords = ["search", "cookie", "accept", "menu", "close", "fermer", "chercher", "annuler", "cancel"]

        best_btn = None
        for btn in buttons:
            text = btn.get("text", "").lower()
            bid = btn.get("id", "").lower()
            bname = btn.get("name", "").lower()
            combined = f"{text} {bid} {bname}"
            
            # Skip buttons that are clearly not submit buttons
            if any(sk in combined for sk in skip_keywords):
                continue
                
            for kw in submit_keywords:
                if kw in combined:
                    best_btn = btn
                    break
            if best_btn: break

        target = best_btn or (buttons[0] if buttons else None)
        if not target:
            return False

        identifier = target.get("id") or target.get("name") or target.get("text")
        print(f"  🖱️ Clicking submit: '{identifier}'")
        
        # Robust click strategy: prioritize actual button elements
        selectors = []
        if target.get("id"): selectors.append(f"#{target['id']}")
        if target.get("name"): selectors.append(f"button[name='{target['name']}'], input[name='{target['name']}']")
        
        # Priority 1: Real button/input tags with this text
        if target.get("text"):
            selectors.append(f"button:has-text('{target['text']}')")
            selectors.append(f"input[value='{target['text']}']")
            selectors.append(f"input[type='submit'][value*='{target['text']}']")
        
        # Priority 2: Any element with this text that has a button role
        if target.get("text"):
            selectors.append(f"[role='button']:has-text('{target['text']}')")
            
        # Last resort: generic text (may hit a header, so we try this last)
        if target.get("text"):
            selectors.append(f"text='{target['text']}'")

        for sel in selectors:
            try:
                success = await self.browser.click_element(sel)
                if success:
                    await asyncio.sleep(1)
                    return True
            except:
                continue
        
        # Final fallback
        return await self.browser.click_element(f"text='{identifier}'")

    async def _fill_fields(self, test_case: dict, page_info: dict, credentials: dict = None):
        steps = test_case.get("steps", [])
        detected_fields = page_info.get("fields", [])
        field_ids = set()
        for f in detected_fields:
            if f.get("id"):
                field_ids.add(f["id"].lower())
            if f.get("name"):
                field_ids.add(f["name"].lower())
            if f.get("placeholder"):
                field_ids.add(f["placeholder"].lower())

        skip_keywords = {
            "submit", "login", "sign in", "register", "submit button",
            "se connecter", "connexion", "s'inscrire", "sign up", "button",
            "login_button", "submit_button", "btn"
        }

        for step in steps:
            field_id = step.get("field", "").strip()
            field_lower = field_id.lower()
            if field_lower in skip_keywords or not field_id:
                continue
            if field_lower not in field_ids and not any(
                field_lower in fid for fid in field_ids
            ):
                continue

            value = step.get("value", "")

            if credentials:
                email = credentials.get("email", "")
                password = credentials.get("password", "")
                value = str(value).replace("{{email}}", email).replace("{{password}}", password)

            try:
                await self.browser.fill_field(field_identifier=field_id, value=value)
            except Exception:
                pass

    async def execute(self, test_case: dict, url: str, page_info: dict, credentials: dict = None) -> dict:
        """Executes a single test case."""
        test_id = test_case.get("id", "TC_UNKNOWN")
        print(f"\n  🧪 {test_id}: {test_case.get('description')}")
        
        try:
            # 1. Fill fields
            await self._fill_fields(test_case, page_info, credentials)
            
            # 2. Click submit
            buttons = await self.browser.get_visible_buttons()
            success = await self.click_submit(buttons)
            
            if not success:
                return {"test_id": test_id, "status": "failed", "error": "Could not find or click submit button"}

            # 3. Wait and verify
            await asyncio.sleep(3)
            page_text = await self.browser.get_page_text()
            current_url = await self.browser.get_page_url()
            
            from tools.llm import verify_result
            verification = verify_result(page_text, page_info.get("language", "en"), {"url": current_url})
            
            # 4. Take screenshot
            screenshot_path = await self.browser.take_screenshot(f"result_{test_id}")
            
            status = "passed" if verification["result"] == "success" else "failed"
            
            if status == "passed":
                print(f"  ✅ {test_id} PASSED: {verification.get('reason')}")
            else:
                print(f"  ❌ {test_id} FAILED: {verification.get('reason')}")

            return {
                "test_id": test_id,
                "status": status,
                "error": verification.get("reason") if status == "failed" else None,
                "screenshot": screenshot_path,
                "url": current_url
            }

        except Exception as e:
            print(f"  💥 Error executing {test_id}: {e}")
            return {"test_id": test_id, "status": "failed", "error": str(e)}