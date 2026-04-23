import re
from tools.llm import generate_test_cases


class Planner:
    def __init__(self):
        pass

    def plan(self, fields: list, url: str, page_info: dict, credentials: dict = None):
        form_type = page_info.get("form_type", "login")
        print(f"[THINK] Generating test cases using LLM...")
        print(f"  Language: {page_info.get('language')} | Form type: {form_type}")
        if credentials:
            print(f"  Credentials: {credentials.get('email')} (will be used for TC001)")

        test_cases = generate_test_cases(fields, url, page_info)

        if credentials:
            test_cases = self._inject_credentials(test_cases, credentials)

        print(f"[THINK] Generated {len(test_cases)} test cases.")
        return test_cases

    def _inject_credentials(self, test_cases: list, credentials: dict) -> list:
        email = credentials.get("email", "")
        password = credentials.get("password", "")

        for tc in test_cases:
            if tc.get("id") in ("TC001", "TC_LOGIN_001", "valid_login", "login_valid"):
                steps = tc.get("steps", [])
                for step in steps:
                    val = step.get("value", "")
                    if "{{email}}" in val:
                        step["value"] = val.replace("{{email}}", email)
                    elif "{{password}}" in val:
                        step["value"] = val.replace("{{password}}", password)
                    elif "{{email}}" in str(val):
                        step["value"] = str(val).replace("{{email}}", email)
                    elif "{{password}}" in str(val):
                        step["value"] = str(val).replace("{{password}}", password)

                    raw_val = str(step.get("value", ""))
                    if "{{email}}" in raw_val:
                        step["value"] = raw_val.replace("{{email}}", email)
                    if "{{password}}" in raw_val:
                        step["value"] = raw_val.replace("{{password}}", password)

        return test_cases