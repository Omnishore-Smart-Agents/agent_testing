import asyncio
from agent.executor import Executor
from agent.reporter import Reporter
from agent.signup_phase import SignupPhase
from tools.browser import BrowserWrapper
from tools.llm import generate_form_data, analyze_page_purpose
class CoreAgent:
    def __init__(self):
        self.browser = BrowserWrapper()
        self.executor = Executor(self.browser)
        self.reporter = Reporter()

    async def run(self, start_url: str):
        try:
            await self.browser.start()

            history = []
            results = []
            credentials = {}  # Will store {"email": ..., "password": ...}

            # ══════════════════════════════════════════════
            # PHASE 1: Open URL & Find Registration
            # ══════════════════════════════════════════════
            # ... (no changes here) ...
            print("\n" + "="*60)
            print("📌 PHASE 1: Opening URL and finding registration page")
            print("="*60)

            await self.browser.open_page(start_url)
            await self.browser.take_screenshot(name="01_initial_page")
            current_url = await self.browser.get_page_url()
            history.append(f"Opened {current_url}")

            # Look for registration link
            reg_links = await self.browser.find_register_link()

            if reg_links:
                print(f"  🔍 Found {len(reg_links)} registration link(s):")
                for link in reg_links:
                    print(f"     → '{link['text']}'")

                # Click the first registration link
                clicked = False
                for link in reg_links:
                    print(f"\n  🖱️ Clicking: '{link['text']}'")
                    success = await self.browser.click_link_element(link["element"])
                    if success:
                        new_url = await self.browser.get_page_url()
                        if new_url != current_url:
                            print(f"  ✅ Navigated to: {new_url}")
                            current_url = new_url
                            clicked = True
                            break
                        else:
                            print(f"  ⚠️ URL didn't change, trying next link...")

                if not clicked:
                    print("  ⚠️ No registration link navigated. Staying on current page.")
                    history.append("Could not navigate to registration page.")
            else:
                print("  ⚠️ No registration link found on this page.")
                history.append("No registration link found.")

            await self.browser.take_screenshot(name="02_after_nav")

            # ══════════════════════════════════════════════
            # PHASE 2: Fill Registration Form
            # ══════════════════════════════════════════════
            print("\n" + "="*60)
            print("📌 PHASE 2: Analyzing and filling the registration form")
            print("="*60)

            fields = await self.browser.get_form_fields()
            buttons = await self.browser.get_visible_buttons()

            if fields:
                print(f"  🔍 Found {len(fields)} form fields:")
                for f in fields:
                    identifier = f.get("name") or f.get("id") or f.get("placeholder", "unknown")
                    print(f"     → [{f['tag']}] {identifier} (type={f.get('type', '-')})")

                # Ask LLM to generate test data
                print("\n  🧠 Asking AI to generate test data...")
                form_data = generate_form_data(fields)

                if form_data:
                    print(f"  📝 Generated data for {len(form_data)} fields")

                    # Save credentials for login phase (take first email and first password only)
                    for key, val in form_data.items():
                        key_lower = key.lower()
                        if "email" in key_lower and "email" not in credentials:
                            credentials["email"] = val
                        elif ("password" in key_lower or "pwd" in key_lower) and "password" not in credentials:
                            credentials["password"] = val

                    # Step 1: Handle custom dropdowns (Title, Country, etc.)
                    print("\n  🎯 Handling custom dropdowns...")
                    handled = await self.browser.handle_custom_dropdowns()
                    if handled:
                        for h in handled:
                            print(f"     ✅ {h}")
                    else:
                        print("     (no custom dropdowns found)")

                    # Step 2: Fill standard form fields
                    print("\n  ✏️ Filling form fields...")
                    fill_results = await self.executor.fill_form(form_data)
                    history.append(f"Filled registration form: {fill_results}")

                    # Step 3: Submit the form
                    print("\n  📤 Submitting form...")
                    
                    # Check for Captcha before submitting
                    has_captcha = await self.browser.is_captcha_present()
                    if has_captcha:
                        print("  🛑 CAPTCHA DETECTED! Cannot proceed autonomously.")
                        history.append("Registration blocked by CAPTCHA.")
                        results.append({
                            "test_id": "REG001", 
                            "description": "Register new account", 
                            "status": "blocked",
                            "error": "Manual CAPTCHA required. Agent cannot bypass this security layer."
                        })
                    else:
                        await self.executor.click_submit(buttons)
                        print("  ⏳ Waiting 10s for automatic redirection to dashboard...")
                        await asyncio.sleep(10) 
                        await self.browser.take_screenshot(name="03_after_registration")

                        # Check result
                        new_url = await self.browser.get_page_url()
                        page_text = (await self.browser.get_page_text()).lower()
                        success_keywords = ["welcome", "bienvenue", "dashboard", "logout", "déconnexion", "mon compte", "profile", "signed in", "connected"]
                        found_success = any(kw in page_text for kw in success_keywords) or "dashboard" in new_url.lower()

                        if found_success or new_url != current_url:
                            print(f"  ✅ Registration successful! (URL: {new_url})")
                            history.append(f"Registration successful. Redirected to {new_url}")
                            results.append({"test_id": "REG001", "description": "Register new account", "status": "passed"})
                        else:
                            print("  ⚠️ Registration may have failed or was too slow.")
                            history.append("Registration may have failed.")
                            results.append({"test_id": "REG001", "description": "Register new account", "status": "failed",
                                            "error": "Form submission did not redirect within 10s"})
                else:
                    print("  ❌ LLM could not generate form data.")
                    results.append({"test_id": "REG001", "description": "Register new account", "status": "failed",
                                    "error": "Could not generate test data"})
            else:
                print("  ⚠️ No form fields found on this page.")
                history.append("No form fields found.")

            # ══════════════════════════════════════════════
            # PHASE 3: Test Login with Created Credentials
            # ══════════════════════════════════════════════
            if credentials.get("email") and credentials.get("password"):
                print("\n" + "="*60)
                print("📌 PHASE 3: Testing login with created credentials")
                print("="*60)

                # Check if we are already logged in (dashboard)
                current_url = await self.browser.get_page_url()
                page_text = (await self.browser.get_page_text()).lower()
                
                print(f"  🔍 Checking session state... Current URL: {current_url}")
                
                success_keywords = ["welcome", "bienvenue", "dashboard", "logout", "déconnexion", "mon compte", "profile", "signed in", "connected"]
                found_kw = [kw for kw in success_keywords if kw in page_text]
                
                # Check by URL or by Text
                is_dashboard_url = "dashboard" in current_url.lower() or "home" in current_url.lower() or "account" in current_url.lower()
                is_logged_in = (len(found_kw) > 0 or is_dashboard_url) and current_url != start_url

                if is_logged_in:
                    print(f"  ✨ SUCCESS: Already logged in! (Detected via {'Keywords: ' + str(found_kw) if found_kw else 'URL: ' + current_url})")
                    results.append({"test_id": "TC001", "description": "Login with valid credentials", "status": "passed"})
                else:
                    # Navigate to login page if not already there
                    if current_url != start_url:
                        print(f"  🔙 Not on dashboard. Navigating back to login: {start_url}")
                        await self.browser.open_page(start_url)
                        await asyncio.sleep(3)

                    login_fields = await self.browser.get_form_fields()
                    login_buttons = await self.browser.get_visible_buttons()
                    
                    # Fill and submit
                    login_data = {}
                    for f in login_fields:
                        field_id = f.get("name") or f.get("id") or ""
                        field_lower = field_id.lower()
                        f_type = f.get("type", "").lower()
                        if "email" in field_lower or f_type == "email" or "user" in field_lower:
                            login_data[field_id] = credentials["email"]
                        elif "pass" in field_lower or f_type == "password":
                            login_data[field_id] = credentials["password"]

                    if login_data:
                        await self.executor.fill_form(login_data)
                        await self.browser.take_screenshot(name="03_login_filled_debug")
                        await self.executor.click_submit(login_buttons)
                        await asyncio.sleep(8)
                        
                        login_url = await self.browser.get_page_url()
                        login_text = (await self.browser.get_page_text()).lower()
                        if any(kw in login_text for kw in success_keywords) or login_url != start_url:
                            print("  ✅ TC001 PASSED: Login successful.")
                            results.append({"test_id": "TC001", "description": "Login with valid credentials", "status": "passed"})
                        else:
                            print("  ❌ TC001 FAILED: Login did not succeed.")
                            results.append({"test_id": "TC001", "description": "Login with valid credentials", "status": "failed"})

                # Navigate back to the original login page
                print(f"  🔙 Navigating back to: {start_url}")
                await self.browser.open_page(start_url)
                await asyncio.sleep(2)

                # Find login form fields
                login_fields = await self.browser.get_form_fields()
                login_buttons = await self.browser.get_visible_buttons()

                if login_fields:
                    # === TEST CASE 1: Valid credentials ===
                    print("\n  🧪 TC001: Login with VALID credentials")
                    await self.browser.context.clear_cookies()
                    await self.browser.open_page(start_url)
                    await asyncio.sleep(2)
                    
                    login_fields = await self.browser.get_form_fields()
                    login_buttons = await self.browser.get_visible_buttons()
                    
                    login_data = {}
                    for f in login_fields:
                        field_id = f.get("name") or f.get("id") or ""
                        field_lower = field_id.lower()
                        f_type = f.get("type", "").lower()
                        if "email" in field_lower or f_type == "email" or "user" in field_lower:
                            login_data[field_id] = credentials["email"]
                        elif "pass" in field_lower or f_type == "password":
                            login_data[field_id] = credentials["password"]

                    if login_data:
                        fill_res = await self.executor.fill_form(login_data)
                        # DEBUG: Take screenshot before clicking to see if fields are filled
                        await self.browser.take_screenshot(name="03_login_filled_debug")
                        
                        await self.executor.click_submit(login_buttons)
                        await asyncio.sleep(8)  # Increased for slow Vercel redirects
                        await self.browser.take_screenshot(name="04_login_valid")

                        login_url = await self.browser.get_page_url()
                        print(f"  📍 Current URL after wait: {login_url}")
                        has_error = await self.browser.has_error_message()
                        login_page_text = (await self.browser.get_page_text()).lower()
                        # Keywords that indicate a successful session
                        success_login_keywords = ["welcome", "bienvenue", "dashboard", "logout", "déconnexion", "mon compte", "profile", "signed in", "connected"]
                        found_login_success = any(kw in login_page_text for kw in success_login_keywords)

                        if (login_url != start_url or found_login_success) and not has_error:
                            print("  ✅ TC001 PASSED: Login with valid credentials succeeded.")
                            results.append({"test_id": "TC001", "description": "Login with valid credentials", "status": "passed"})
                        else:
                            print(f"  ❌ TC001 FAILED: Login did not succeed (Current URL: {login_url}).")
                            results.append({"test_id": "TC001", "description": "Login with valid credentials", "status": "failed",
                                            "error": f"Login did not redirect or show success message. URL is still {login_url}"})

                    # === TEST CASE 2: Invalid password ===
                    print("\n  🧪 TC002: Login with INVALID password")
                    await self.browser.context.clear_cookies()
                    await self.browser.open_page(start_url)
                    await asyncio.sleep(2)

                    login_fields = await self.browser.get_form_fields()
                    login_buttons = await self.browser.get_visible_buttons()
                    invalid_data = {}
                    for f in login_fields:
                        field_id = f.get("name") or f.get("id") or ""
                        field_lower = field_id.lower()
                        f_type = f.get("type", "").lower()
                        if "email" in field_lower or f_type == "email" or "user" in field_lower:
                            invalid_data[field_id] = credentials["email"]
                        elif "pass" in field_lower or f_type == "password":
                            invalid_data[field_id] = "WrongPassword123!"

                    if invalid_data:
                        fill_res = await self.executor.fill_form(invalid_data)
                        await self.executor.click_submit(login_buttons)
                        await asyncio.sleep(2)
                        await self.browser.take_screenshot(name="05_login_invalid")

                        has_error = await self.browser.has_error_message()
                        if has_error:
                            print("  ✅ TC002 PASSED: Invalid password correctly rejected.")
                            results.append({"test_id": "TC002", "description": "Login with invalid password", "status": "passed"})
                        else:
                            print("  ❌ TC002 FAILED: No error shown for invalid password.")
                            results.append({"test_id": "TC002", "description": "Login with invalid password", "status": "failed",
                                            "error": "No error message displayed"})

                    # === TEST CASE 3: Empty fields ===
                    print("\n  🧪 TC003: Login with EMPTY fields")
                    await self.browser.context.clear_cookies()
                    await self.browser.open_page(start_url)
                    await asyncio.sleep(2)

                    login_buttons = await self.browser.get_visible_buttons()
                    await self.executor.click_submit(login_buttons)
                    await asyncio.sleep(2)
                    await self.browser.take_screenshot(name="06_login_empty")

                    has_error = await self.browser.has_error_message()
                    same_url = (await self.browser.get_page_url()) == start_url or has_error
                    if same_url:
                        print("  ✅ TC003 PASSED: Empty submission correctly rejected.")
                        results.append({"test_id": "TC003", "description": "Login with empty fields", "status": "passed"})
                    else:
                        print("  ❌ TC003 FAILED: Empty submission was not rejected.")
                        results.append({"test_id": "TC003", "description": "Login with empty fields", "status": "failed",
                                        "error": "Form accepted empty fields"})

            else:
                print("\n  ⚠️ No credentials saved. Skipping login tests.")
                history.append("Skipped login tests - no credentials from registration.")

            # DEBUG: Force a failure for Trello test
          #  results.append({
           ##    "description": "Simulation d'erreur pour tester Trello",
             #   "status": "failed",
              #  "error": "L'agent a détecté une anomalie critique (Simulation)",
               # "screenshot": "output/screenshots/03_login_filled_debug.png"
            #})

            # ══════════════════════════════════════════════
            # PHASE 4: Generate Report
            # ══════════════════════════════════════════════
            print("\n" + "="*60)
            print("📌 PHASE 4: Generating test report")
            print("="*60)

            final_report = self.reporter.report(results)
            final_report["history"] = history
            final_report["credentials_used"] = credentials
            return final_report

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\n💥 Agent failed critically: {repr(e)}")
            return {"error": repr(e)}
        finally:
            await self.browser.close()