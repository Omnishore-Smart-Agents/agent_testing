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
