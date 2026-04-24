class Planner:
    """Plans the next action. In the new architecture, planning is done directly in CoreAgent."""
    def __init__(self):
        pass

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