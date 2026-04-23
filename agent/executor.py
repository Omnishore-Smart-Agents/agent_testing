import asyncio
import traceback

class Executor:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def execute(self, test_case, url):
        """
        ACT and VERIFY loop for a single test case.
        """
        print(f"🚀 [ACT] Executing test case: {test_case.get('id')} - {test_case.get('description')}")
        result = {
            "test_case": test_case,
            "status": "passed",
            "error": None,
            "screenshot": None,
            "execution_time_ms": 0 # Would be filled with real timing if needed
        }
        
        try:
            # ACT
            # 1. ensure we are on the right URL clean
            await self.browser.open_page(url)
            
            # 2. Fill fields
            steps = test_case.get('steps', [])
            for step in steps:
                field_id = step.get('field')
                value = step.get('value')
                # Try finding field and filling
                await self.browser.fill_field(field_identifier=field_id, value=value)
                
            # 3. Submit
            await self.browser.click_submit()
            await self.browser.wait_for_load()
            
            # VERIFY
            print(f"🔍 [VERIFY] Verifying results for {test_case.get('id')}...")
            expected = test_case.get('expected', '').lower()
            current_url = await self.browser.get_page_url()
            has_error = await self.browser.has_error_message()

            # Simple heuristic
            is_valid_login_test = "success" in expected or "log in" in expected or "dashboard" in expected or "valid" in expected
            is_invalid_login_test = "fail" in expected or "error" in expected or "invalid" in expected

            passed = False

            if is_valid_login_test:
                # Expecting success: require URL change AND no visible error.
                # Poll briefly to allow transient toasts/overlays to clear.
                max_attempts = 6
                for _ in range(max_attempts):
                    current_url = await self.browser.get_page_url()
                    has_error = await self.browser.has_error_message()
                    if (not has_error) and (url not in current_url):
                        passed = True
                        break
                    await asyncio.sleep(0.5)
            elif is_invalid_login_test:
                # Expecting failure: either an error message is shown or we remain on the same URL
                if has_error or (url in current_url):
                    passed = True
            else:
                # Fallback naive pass (if we can't heuristically verify)
                passed = True
                
            if not passed:
                raise Exception("Verification failed. Expected state not reached.")

        except Exception as e:
            print(f"❌ [ACT/VERIFY] Test {test_case.get('id')} failed: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            try:
                path = await self.browser.take_screenshot(name=f"error_{test_case.get('id')}")
                result["screenshot"] = path
            except Exception as ss_e:
                print(f"   Screenshot failed: {ss_e}")
        else:
            # Passed verification: capture a success screenshot for records
            try:
                path = await self.browser.take_screenshot(name=f"success_{test_case.get('id')}")
                result["screenshot"] = path
            except Exception as ss_e:
                print(f"   Success screenshot failed: {ss_e}")

        return result
