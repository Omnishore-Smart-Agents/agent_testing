import asyncio
import hashlib
from tools.llm import verify_result


class Executor:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def execute(self, test_case: dict, url: str, page_info: dict, credentials: dict = None):
        tc_id = test_case.get("id", "unknown")
        print(f"🚀 [ACT] Executing: {tc_id} - {test_case.get('description')}")

        result = {
            "test_case": test_case,
            "status": "passed",
            "error": None,
            "screenshots": [],
        }

        try:
            await self.browser.reset_session()
            await self.browser.open_page(url)
            await self.browser.dismiss_cookies()

            ss_before = await self.browser.take_screenshot(f"{tc_id}_before_login")
            result["screenshots"].append({
                "label": "form_before_login",
                "url": await self.browser.get_page_url(),
                "page_title": await self.browser.get_page_title(),
                "path": ss_before,
            })

            await self._fill_fields(test_case, page_info, credentials)

            ss_filled = await self.browser.take_screenshot(f"{tc_id}_filled")
            result["screenshots"].append({
                "label": "form_filled",
                "url": await self.browser.get_page_url(),
                "page_title": await self.browser.get_page_title(),
                "path": ss_filled,
            })

            lang = page_info.get("language", "en")
            await self.browser.click_submit(lang=lang)

            original_url = url
            original_content_hash = hashlib.md5((await self.browser.get_page_text()).lower().encode()).hexdigest()

            for _ in range(15):
                await asyncio.sleep(1)
                current_text = (await self.browser.get_page_text()).lower()
                current_hash = hashlib.md5(current_text.encode()).hexdigest()
                if current_hash != original_content_hash:
                    break
                if await self.browser.has_error_message():
                    break

            ss_after = await self.browser.take_screenshot(f"{tc_id}_after_submit")
            page_text = await self.browser.get_page_text()
            final_url = await self.browser.get_page_url()
            page_title = await self.browser.get_page_title()

            has_error = await self.browser.has_error_message()
            if has_error:
                label = "error_state"
            elif original_url not in final_url:
                label = "page_after_login"
            else:
                label = "page_after_submit"

            result["screenshots"].append({
                "label": label,
                "url": final_url,
                "page_title": page_title,
                "path": ss_after,
            })

            print(f"🔍 [VERIFY] Verifying: {tc_id}...")

            verification = test_case.get("verification", {})
            url_change_expected = verification.get("url_change", True)

            llm_result = verify_result(page_text, lang, verification)

            passed = False
            if llm_result["result"] == "success":
                passed = url_change_expected
            elif llm_result["result"] == "failure":
                passed = not url_change_expected
            else:
                for _ in range(10):
                    await asyncio.sleep(0.5)
                    current_url = await self.browser.get_page_url()
                    page_text = await self.browser.get_page_text()
                    if original_url not in current_url:
                        passed = url_change_expected
                        break
                    if await self.browser.has_error_message():
                        passed = not url_change_expected
                        break
                else:
                    passed = not url_change_expected

            if not passed:
                ss_error = await self.browser.take_screenshot(f"{tc_id}_error")
                result["screenshots"].append({
                    "label": "error_state",
                    "url": await self.browser.get_page_url(),
                    "page_title": await self.browser.get_page_title(),
                    "path": ss_error,
                })
                raise Exception(f"Verification failed: {llm_result.get('reason', 'expected state not reached')}")

        except Exception as e:
            print(f"❌ [ACT/VERIFY] Test {tc_id} failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)

        return result

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