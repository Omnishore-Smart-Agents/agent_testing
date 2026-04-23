import os
import json
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant")

def generate_test_cases(fields, url):
    """
    Given an array of field dictionaries and a target URL,
    ask the LLM to generate at least 3 test cases:
    - valid login
    - invalid login
    - empty fields
    Returns a list of dicts.
    """
    model = get_llm()
    system_prompt = """
    You are an expert QA Automation Engineer.
    Return ONLY a valid JSON array of test case objects. Do not include markdown blocks like ```json or trailing text.
    Each object must have the following keys:
    - id: string (e.g. TC001)
    - description: string
    - steps: array of objects {"field": "name/id/placeholder", "value": "test data"}
    - expected: string
    
    You MUST include at least:
    1. A valid login attempt
    2. An invalid login attempt (wrong credentials)
    3. An attempt with empty fields
    """

    human_prompt = f"""
    Target URL: {url}
    Fields Detected: {json.dumps(fields, indent=2)}
    
    Generate the test cases JSON array now. Make sure the 'field' in steps precisely matches the id or name of the detected fields.
    """
    
    response = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])
    
    raw = response.content.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM: {raw}")
        raise e
