from agent.observer import Observer
from agent.planner import Planner
from agent.executor import Executor
from agent.reporter import Reporter
from agent.signup_phase import SignupPhase
from tools.browser import BrowserWrapper


class CoreAgent:
    def __init__(self):
        self.browser = BrowserWrapper()
        self.observer = Observer(self.browser)
        self.planner = Planner()
        self.reporter = Reporter()

    async def run(self, url: str):
        try:
            await self.browser.start()

            print("=" * 60)
            print("PHASE 1/3: OBSERVE LOGIN PAGE")
            print("=" * 60)
            page_info = await self.observer.observe(url)
            fields = page_info["fields"]
            form_type = page_info["form_type"]

            if not fields:
                return {"error": "No input fields found", "page_info": page_info}

            credentials = None

            if form_type in ("login", "unknown", "signup"):
                print("\n" + "=" * 60)
                print("PHASE 2/3: CREATE ACCOUNT VIA SIGNUP")
                print("=" * 60)
                signup = SignupPhase(self.browser)
                credentials = await signup.run(url, fields, page_info)

                if credentials:
                    print(f"✅ Account created: {credentials['email']}")
                else:
                    print("⚠️ Could not create account — will use generated test credentials")

            if not credentials:
                print("\n" + "=" * 60)
                print("PHASE 2/3: USING DEFAULT TEST CREDENTIALS")
                print("=" * 60)
                credentials = {
                    "email": f"test_{abs(hash(url)) % 100000:05d}@test.com",
                    "password": f"T3st!Pass{int.from_bytes(bytes(str(url), 'utf8'), 'little') % 100000:05d}",
                }
                print(f"Using fallback credentials: {credentials['email']}")

            print("\n" + "=" * 60)
            print("PHASE 3/3: RUN TEST CASES")
            print("=" * 60)
            test_cases = self.planner.plan(fields, url, page_info, credentials=credentials)
            if not test_cases:
                return {"error": "No test cases generated", "page_info": page_info}

            results = []
            for test in test_cases:
                executor = Executor(self.browser)
                res = await executor.execute(test, url, page_info, credentials=credentials)
                results.append(res)
                await self.browser.reset_session()

            final_report = self.reporter.report(results, url=url)
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