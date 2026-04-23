from tools.llm import generate_test_cases

class Planner:
    def __init__(self):
        pass

    def plan(self, fields, url):
        """
        Uses LLM to generate test cases based on observed fields.
        """
        print(f"[THINK] Generating test cases using LLM for {len(fields)} fields...")
        test_cases = generate_test_cases(fields, url)
        print(f"[THINK] Generated {len(test_cases)} test cases.")
        return test_cases
