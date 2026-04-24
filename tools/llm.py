import os
import json
import re
import json_repair
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.1-8b-instant"


def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",  # Much smarter than 8B
        temperature=0.1,  # Low temperature for consistent outputs
    )


def generate_form_data(fields: list) -> dict:
    """
    Given a list of form fields, ask the LLM to generate realistic test data.
    Returns a dict mapping field identifier -> value.
    """
    model = get_llm()

    prompt = (
        "You are a QA test data generator. Given form fields, generate realistic fake data for each.\n"
        "Rules:\n"
        "- For email fields: use a unique fake email like qa_tester_" + str(int(__import__('time').time()))[-5:] + "@gmail.com\n"
        "- For password fields: use a strong password like RoyalAir@2025!\n"
        "- For name fields: use realistic names like Omar, Mansouri\n"
        "- For phone fields: use +212612345678\n"
        "- For birthdateYear: use a year between 1970 and 2000 (User must be an ADULT).\n"
        "- For birthdateDay: use a value between 1 and 28.\n"
        "- For select dropdowns (tag: select): pick one of the 'value' strings provided in the 'options' list. If the list contains '<liferay-ui:message...', pick a simple numeric value if available.\n"
        "- SKIP checkbox/radio/hidden fields\n\n"
        "RETURN ONLY a JSON object mapping each field identifier (id or name) to its generated value.\n"
        "Do NOT add any text before or after the JSON.\n\n"
        f"Form fields:\n{json.dumps(fields, ensure_ascii=False)}\n"
    )

    response = model.invoke([HumanMessage(content=prompt)])
    raw = response.content

    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        return json_repair.loads(raw)
    except Exception:
        print(f"[LLM] Failed to parse form data: {raw[:200]}")
        return {}


def analyze_page_purpose(url: str, page_text_snippet: str, fields_summary: str) -> str:
    """
    Ask the LLM what type of page this is and what to do.
    Returns: 'registration', 'login', 'dashboard', 'other'
    """
    model = get_llm()

    prompt = (
        "What type of page is this? Analyze the URL and visible text.\n"
        f"URL: {url}\n"
        f"Visible text (first 500 chars): {page_text_snippet[:500]}\n"
        f"Form fields: {fields_summary}\n\n"
        "Reply with ONLY one word: registration, login, dashboard, or other."
    )

    response = model.invoke([HumanMessage(content=prompt)])
    result = response.content.strip().lower()

    for page_type in ["registration", "login", "dashboard"]:
        if page_type in result:
            return page_type
    return "other"


def generate_valid_signup_data(fields: list, url: str, page_info: dict) -> dict:
    """
    Asks the LLM to generate all necessary data for a signup form based on extracted fields.
    """
    model = get_llm()
    
    prompt = (
        "You are a specialized QA data generator for registration forms.\n"
        f"Context: URL={url}, Page Info={json.dumps(page_info)}\n"
        f"Form Fields: {json.dumps(fields)}\n\n"
        "Rules:\n"
        "1. Generate a realistic account with email, password, firstname, lastname, phone, address, etc.\n"
        "2. Use a unique email: qa_tester_" + str(int(__import__('time').time()))[-5:] + "@gmail.com\n"
        "3. Strong password: RoyalAir@2025!\n"
        "4. RETURN ONLY a JSON object with these keys: email, password, firstname, lastname, phone, country, city, zip, address, birthdate, gender, terms (bool), newsletter (bool), and a 'fields' list.\n"
        "   IMPORTANT: Each item in the 'fields' list MUST be an object: {\"field\": \"id_or_name_of_field\", \"value\": \"generated_value\"}.\n"
    )

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        raw = response.content
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json_repair.loads(match.group(0))
    except Exception as e:
        print(f"[LLM] Error generating signup data: {e}")
    
    return {}


def verify_result(page_text: str, lang: str, context: dict) -> dict:
    """
    Analyzes page text after an action to determine if it was a success or failure.
    """
    model = get_llm()
    
    prompt = (
        "Analyze this page content after a signup/login attempt.\n"
        f"Language: {lang}\n"
        f"Context: {json.dumps(context)}\n"
        f"Page Text Snippet: {page_text[:1000]}\n\n"
        "Determine if the action was a 'success' or 'failure'.\n"
        "If failure, identify the error type: 'invalid_credentials', 'email_exists', 'captcha', 'field_error', etc.\n"
        "RETURN ONLY a JSON object: {\"result\": \"success\"/\"failure\", \"error_type\": \"...\", \"reason\": \"...\"}"
    )

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        raw = response.content
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            return json_repair.loads(match.group(0))
    except Exception as e:
        print(f"[LLM] Error verifying result: {e}")
        
    return {"result": "failure", "error_type": "unknown", "reason": "LLM failed to verify"}


def detect_page_info(url: str, text: str, fields: list) -> dict:
    """
    Analyzes page content to detect language, purpose, and other metadata.
    """
    model = get_llm()
    prompt = (
        "Analyze this web page state.\n"
        f"URL: {url}\n"
        f"Text Snippet: {text[:800]}\n"
        f"Fields: {json.dumps(fields)}\n\n"
        "Return a JSON object: {\"language\": \"fr/en\", \"direction\": \"ltr/rtl\", \"form_type\": \"login/signup/other\", \"labels\": {\"field_id\": \"label_text\"}}"
    )
    try:
        response = model.invoke([HumanMessage(content=prompt)])
        match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if match:
            return json_repair.loads(match.group(0))
    except:
        pass
    return {"language": "en", "direction": "ltr", "form_type": "other", "fields": fields}


def generate_test_cases(fields: list, url: str, page_info: dict) -> list:
    """
    Generates test cases for login or registration.
    """
    model = get_llm()
    form_type = page_info.get("form_type", "login")
    
    prompt = (
        f"Generate 3 QA test cases for this {form_type} form.\n"
        f"URL: {url}\n"
        f"Fields: {json.dumps(fields)}\n\n"
        "Rules:\n"
        "1. TC001 must be the 'Valid' case (use placeholders {{email}} and {{password}}).\n"
        "2. TC002 must be an 'Invalid' case (wrong password).\n"
        "3. TC003 must be 'Empty' fields.\n"
        "RETURN ONLY a JSON array of objects: [{\"id\": \"TC001\", \"description\": \"...\", \"steps\": [{\"field\": \"...\", \"value\": \"...\"}], \"expected\": \"...\"}]"
    )

    try:
        response = model.invoke([HumanMessage(content=prompt)])
        match = re.search(r'\[.*\]', response.content, re.DOTALL)
        if match:
            return json_repair.loads(match.group(0))
    except:
        pass
    return []
