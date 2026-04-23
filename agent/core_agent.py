from agent.observer import Observer
from agent.planner import Planner
from agent.executor import Executor
from agent.reporter import Reporter
from tools.browser import BrowserWrapper

class CoreAgent:
    def __init__(self):
        self.browser = BrowserWrapper()
        self.observer = Observer(self.browser)
        self.planner = Planner()
        self.executor = Executor(self.browser)
        self.reporter = Reporter()

    async def run(self, url: str):
        try:
            # Setup
            await self.browser.start()
            
            # OBSERVE
            fields = await self.observer.observe(url)
            
            if not fields:
                print("[ERROR] No input fields detected to test.")
                return {"error": "No input fields found"}

            # THINK (Plan)
            test_cases = self.planner.plan(fields, url)
            
            # ACT & VERIFY
            results = []
            for test in test_cases:
                res = await self.executor.execute(test, url)
                results.append(res)
                
            # REPORT
            final_report = self.reporter.report(results)
            return final_report
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Agent failed critically: {repr(e)}")
            return {"error": repr(e)}
        finally:
            await self.browser.close()
