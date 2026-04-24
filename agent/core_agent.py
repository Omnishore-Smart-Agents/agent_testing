from agent.observer import Observer
from agent.planner import Planner
from agent.executor import Executor
from agent.reporter import Reporter
from agent.signup_phase import SignupPhase
from tools.browser import BrowserWrapper


class CoreAgent:
    def __init__(self, browser_type: str = "chromium", log_callback=None):
        self.browser = BrowserWrapper(browser_type=browser_type)
        self.observer = Observer(self.browser)
        self.planner = Planner()
        self.reporter = Reporter()
        self.log_callback = log_callback

    def log(self, message: str):
        if self.log_callback:
            self.log_callback(message)
        print(message)

    async def run(self, url: str, markdown_spec: str = None):
        try:
            await self.browser.start()
            
            # Clean up old screenshots before new run
            import shutil
            import os
            screenshots_dir = "output/screenshots"
            if os.path.exists(screenshots_dir):
                shutil.rmtree(screenshots_dir)
            os.makedirs(screenshots_dir, exist_ok=True)

            self.log("=" * 60)
            self.log("PHASE 1/3: OBSERVE LOGIN PAGE")
            self.log("=" * 60)
            
            # Use markdown_spec to extract page info if provided, otherwise scrape
            if markdown_spec:
                self.log("[INFO] Using markdown specification for test generation")
                page_info = self._parse_markdown_spec(markdown_spec, url)
            else:
                page_info = await self.observer.observe(url)
            
            fields = page_info["fields"]
            form_type = page_info["form_type"]
            self.log(f"Browser: {self.browser.browser_type}")
            self.log(f"Language: {page_info.get('language', 'unknown')} ({page_info.get('direction', 'ltr')}) | Form type: {form_type}")
            self.log(f"Detected {len(fields)} fields")

            if not fields:
                return {"error": "No input fields found", "page_info": page_info}

            credentials = None

            if form_type in ("login", "unknown", "signup"):
                self.log("\n" + "=" * 60)
                self.log("PHASE 2/3: CREATE ACCOUNT VIA SIGNUP")
                self.log("=" * 60)
                signup = SignupPhase(self.browser)
                credentials = await signup.run(url, fields, page_info)

                if credentials:
                    self.log(f"✅ Account created: {credentials['email']}")
                else:
                    self.log("⚠️ Could not create account — will use generated test credentials")

            if not credentials:
                self.log("\n" + "=" * 60)
                self.log("PHASE 2/3: USING DEFAULT TEST CREDENTIALS")
                self.log("=" * 60)
                credentials = {
                    "email": f"test_{abs(hash(url)) % 100000:05d}@test.com",
                    "password": f"T3st!Pass{int.from_bytes(bytes(str(url), 'utf8'), 'little') % 100000:05d}",
                }
                self.log(f"Using fallback credentials: {credentials['email']}")

            # Force login test cases if we're on signup page (user wants to test login, not signup)
            current_form_type = page_info.get("form_type", "login")
            if current_form_type == "signup":
                self.log("[INFO] URL is signup page - will generate LOGIN test cases to test authentication")
                page_info = {**page_info, "form_type": "login"}

            self.log("\n" + "=" * 60)
            self.log("PHASE 3/3: RUN TEST CASES")
            self.log("=" * 60)
            test_cases = self.planner.plan(fields, url, page_info, credentials=credentials)
            if not test_cases:
                return {"error": "No test cases generated", "page_info": page_info}

            self.log(f"[THINK] Generated {len(test_cases)} test cases.")
            results = []
            for test in test_cases:
                executor = Executor(self.browser)
                res = await executor.execute(test, url, page_info, credentials=credentials)
                results.append(res)
                await self.browser.reset_session()

            final_report = self.reporter.report(results, url=url)
            final_report["browser"] = self.browser.browser_type
            final_report["page_info"] = page_info
            final_report["created_credentials"] = {
                "email": credentials.get("email") if credentials else None
            }
            return final_report

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"error": repr(e)}
        finally:
            await self.browser.close()

    def _parse_markdown_spec(self, markdown: str, url: str) -> dict:
        """Parse markdown specification to extract page info and test requirements."""
        import re
        
        page_info = {
            "url": url,
            "language": "en",
            "direction": "ltr",
            "form_type": "login",
            "fields": [],
            "labels": {},
            "submit_buttons": [],
            "page_title": ""
        }
        
        # Extract form type
        form_type_match = re.search(r'##\s*Form\s+Type\s*\n(.*?)(?=\n##|\Z)', markdown, re.IGNORECASE | re.DOTALL)
        if form_type_match:
            form_type_text = form_type_match.group(1).strip().lower()
            if 'signup' in form_type_text or 'register' in form_type_text:
                page_info["form_type"] = "signup"
            elif 'reset' in form_type_text or 'password' in form_type_text:
                page_info["form_type"] = "reset"
            elif 'login' in form_type_text or 'signin' in form_type_text:
                page_info["form_type"] = "login"
        
        # Extract fields from table or list
        field_patterns = [
            (r'\|\s*(\w+)\s*\|.*?\|\s*(\w+)\s*\|', re.MULTILINE | re.DOTALL),
            (r'-\s*(\w+)\s*\(type:\s*(\w+)', 0),
            (r'\*\s*(\w+)\s*\(type:\s*(\w+)', 0),
            (r'(\w+)\s*:\s*(\w+)', 0),
        ]
        
        extracted_fields = set()
        
        for pattern, flags in field_patterns:
            matches = re.findall(pattern, markdown, re.IGNORECASE | flags)
            for match in matches:
                if len(match) >= 2:
                    field_name = match[0].strip().lower()
                    field_type = match[1].strip().lower()
                    if field_name not in extracted_fields and field_name not in ['field', 'type', 'required', 'description']:
                        extracted_fields.add(field_name)
                        page_info["fields"].append({
                            "name": field_name,
                            "type": field_type,
                            "required": True
                        })
        
        # Extract submit button text
        button_match = re.search(r'(?:submit|login|register|sign\s*in)\s*button', markdown, re.IGNORECASE)
        if button_match:
            page_info["submit_buttons"].append({
                "text": button_match.group(0),
                "type": "submit"
            })
        
        # Extract language
        lang_match = re.search(r'##\s*Language\s*\n(.*?)(?=\n##|\Z)', markdown, re.IGNORECASE | re.DOTALL)
        if lang_match:
            page_info["language"] = lang_match.group(1).strip().lower()[:2]
        
        self.log(f"[PARSED] From markdown: {len(page_info['fields'])} fields, form_type={page_info['form_type']}")
        return page_info