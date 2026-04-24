import os
import json
import uuid
import re
from datetime import datetime
from langchain_groq import ChatGroq
from langchain.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

MODEL = "llama-3.1-8b-instant"


def get_llm():
    return ChatGroq(api_key=os.getenv("GROQ_API_KEY"), model=MODEL)


def detect_page_info(url: str, page_text: str) -> dict:
    model = get_llm()
    system_prompt = """You are a language detection and form analysis specialist.
Return ONLY a valid JSON object — no markdown, no explanation, no extra text.
The JSON must have these exact keys:
{
  "language": "en" | "fr" | "ar" | "es" | "de" | "pt" | "it" | "zh" | "ja" | "ko" | "ru" | "tr" | "nl" | "pl" | "uk",
  "direction": "ltr" | "rtl",
  "form_type": "login" | "signup" | "reset_password" | "contact" | "unknown",
  "labels": { "field_name_or_id": "visible label text" },
  "submit_buttons": ["button text 1", "button text 2"],
  "page_title": "detected page title or main heading",
  "signup_url_hint": "relative or absolute URL found for signup/register page, or null"
}"""
    human_prompt = f"URL: {url}\n\nPage text content:\n{page_text[:3000]}"
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    raw = response.content.replace("```json", "").replace("```", "").strip()
    print(f"[DEBUG] detect_page_info raw: {raw[:300]}...")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print(f"[DEBUG] detect_page_info failed to parse")
        return {
            "language": "en", "direction": "ltr", "form_type": "unknown",
            "labels": {}, "submit_buttons": [], "page_title": "", "signup_url_hint": None
        }


def generate_valid_signup_data(fields: list, url: str, page_info: dict) -> dict:
    model = get_llm()
    lang = page_info.get("language", "en")
    direction = page_info.get("direction", "ltr")

    system_prompt = f"""You are a QA test data generator for signup/registration forms.
Page language: {lang} | Page direction: {direction}
Generate ONE valid registration data set that will successfully create an account.

CRITICAL: You MUST generate realistic test data for ALL these fields if they exist in the form:

NAME FIELDS (firstname/lastname):
- firstname / first_name / firstName / fname / prenom / Prénom / name / Nom / lastname / last_name / lastName / lname
- Always generate BOTH firstname AND lastname for full name forms

EMAIL FIELDS:
- email / emailAddress / email_address / e-mail / EmailAddress / username (if for login)
- Generate valid unique email: test_YYYYMMDDHHMMSS_XXXX@example.com

PASSWORD FIELDS:
- password / motdepasse / pass / mot_de_passe / passwordInput / userPassword / Password
- password_confirm / password_confirmation / confirm_password / confirmation_mot_de_passe / confirmPassword
- Generate STRONG password: min 8 chars, must have uppercase + lowercase + number + special char (!@#$%^&*)
- Example: Test@Pass2024

PHONE/TELEPHONE FIELDS:
- phone / telephone / tel / mobile / phoneNumber / téléphone / numéro / phone-number / tel-input
- phone_mobile / mobile_phone / contact_phone / numero_telephone / tel_portable
- phone is CRITICAL - many sites require valid phone format

COUNTRY/REGION FIELDS:
- country / pays / countryCode / country_code / countryId / select-country / country-select / pays_id
- address_country / countryName / libelle_pays

CITY/TOWN FIELDS:
- city / ville / town / locality / municipality / localityName / ville_id / locality_name
- address_city / cityInput / ville_input

ZIP/POSTAL CODE FIELDS:
- zip / zipcode / postal_code / code_postal / postalCode / zip_code / code_postal_input

ADDRESS FIELDS:
- address / adresse / street / streetAddress / address1 / address_line1 / adresse_rue

USERNAME FIELDS (if not email):
- username / usernameInput / user_name / pseudo

DATE OF BIRTH / BIRTHDAY:
- birthdate / birthday / date_naissance / birth_date / dob / dateOfBirth / birthdayDate

GENDER:
- gender / genre / Civilité / civilité / sex / genderSelect

TERMS/NEWSLETTER CHECKBOXES:
- terms / cgu / conditions / accept_terms / accept_cgu / newsletter / newsletter_optin

Generate REALISTIC data matching the page language/country:
- French (fr): na￼
Chromium history
Tabs from other devices
Delete browsing data
By date
By group
mes like Jean/Marie/Pierre, phone +33612345678, cities Paris/Lyon/Marseille
- Arabic (ar): names like محمد/فاطمة/عمر, phone +212612345678, cities الدار البيضاء/الرباط/مراكش
- Spanish (es): names like Juan/María/Pedro, phone +34612345678, cities Madrid/Barcelona/Valencia
- English (en): names like John/Mary/Peter, phone +15551234567, cities New York/Los Angeles/London

PHONE FORMAT IS CRITICAL - MUST BE VALID:
- France: +33612345678 (10 digits, starts with +33 or 06)
- Morocco: +212612345678 (12 digits, starts with +212 or 06)
- Spain: +34612345678 (11 digits, starts with +34 or 6)
- UK: +447700123456 (12 digits, starts with +44 or 07)
- US: +15551234567 (11 digits, starts with +1)

Do NOT include fields named: submit, button, register, login, sign up, btn, submitButton, submit-button - those are buttons.

Return ONLY valid JSON (no markdown):
{{
  "email": "test_YYYYMMDDHHMMSS_XXXX@example.com",
  "password": "Test@Pass2024",
  "firstname": "Jean",
  "lastname": "Dupont",
  "phone": "+33612345678",
  "country": "FR",
  "city": "Paris",
  "zip": "75001",
  "address": "123 Rue de la Paix",
  "birthdate": "15/06/1990",
  "gender": "M",
  "newsletter": true,
  "terms": true,
  "fields": [{{"field": "html_name_or_id", "value": "field_value"}}],
  "raw_data": {{"email": "...", "password": "...", "firstname": "...", "lastname": "...", "phone": "...", "country": "...", "city": "..."}}
}}
"""
    fields_json = json.dumps(fields, indent=2)
    human_prompt = f"URL: {url}\nFields: {fields_json}"
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    raw = response.content.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
        data.setdefault("firstname", "Jean")
        data.setdefault("lastname", "Dupont")
        data.setdefault("phone", "+33612345678")
        data.setdefault("country", "FR")
        data.setdefault("city", "Paris")
        data.setdefault("zip", "75001")
        data.setdefault("address", "123 Rue de la Paix")
        data.setdefault("birthdate", "15/06/1990")
        data.setdefault("gender", "M")
        data.setdefault("terms", True)
        return data
    except json.JSONDecodeError:
        return {
            "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
            "password": f"T3st@{uuid.uuid4().hex[:6]}",
            "firstname": "Jean",
            "lastname": "Dupont",
            "phone": "+33612345678",
            "country": "FR",
            "city": "Paris",
            "zip": "75001",
            "address": "123 Rue de la Paix",
            "fields": [],
            "raw_data": {}
        }


def generate_test_cases(fields: list, url: str, page_info: dict) -> list:
    model = get_llm()
    lang = page_info.get("language", "en")
    form_type = page_info.get("form_type", "login")
    
    print(f"[DEBUG] generate_test_cases: form_type={form_type}, lang={lang}, fields={len(fields)}")
    print(f"[DEBUG] URL being tested: {url}")

    # Always generate LOGIN test cases regardless of form_type detected on page
    # User wants to test authentication
    if form_type == "signup":
        print(f"[DEBUG] Forcing login test cases (form was signup)")
        return _generate_login_cases(model, fields, url, lang)
    elif form_type == "reset_password":
        return _generate_reset_cases(model, fields, url, lang)
    else:
        return _generate_login_cases(model, fields, url, lang)


def _generate_login_cases(model, fields, url, lang):
    system_prompt = f"""You are an expert QA Automation Engineer.
Page language: {lang}
Return ONLY a valid JSON array of test case objects. No markdown.

Required test cases:
1. TC001: Valid login (use real-looking email like "testuser123@example.com" and password like "TestPass123!")
2. TC002: Invalid login (wrong password — use the same email as TC001 and "WrongPass123!")
3. TC003: Invalid login (wrong email — use "nonexistent.user@example.com" and the password from TC001)
4. TC004: Empty username/email field
5. TC005: Empty password field
6. TC006: Empty both fields
7. TC007: SQL injection in email field (use "' OR 1=1 --" as email)
8. TC008: XSS in password field (use "<script>alert(1)</script>" as password)

Each object must have:
- id: string (TC001, TC002...)
- description: string in {lang}
- steps: [{{"field": "name_or_id_or_placeholder", "value": "test data"}}]
- expected: string in {lang} describing outcome
- verification: {{"url_change": true|false, "error_patterns": ["error text in {lang} to look for"]}}
"""
    fields_json = json.dumps(fields, indent=2)
    human_prompt = f"URL: {url}\nFields detected: {fields_json}"
    print(f"[DEBUG] Calling LLM for login test cases, fields={fields_json[:200]}...")
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    print(f"[DEBUG] LLM response: {response.content[:300]}...")
    return _parse_json_response(response.content)


def _generate_signup_cases(model, fields, url, lang):
    system_prompt = f"""You are an expert QA Automation Engineer.
Page language: {lang}
Return ONLY a valid JSON array of test case objects. No markdown.

Required test cases:
1. TC_REG_001: Valid registration with all fields filled correctly
2. TC_REG_002: Email already registered (use a well-known email like test@test.com)
3. TC_REG_003: Password too short (<8 chars)
4. TC_REG_004: Password without uppercase letter
5. TC_REG_005: Password without number
6. TC_REG_006: Password confirmation mismatch
7. TC_REG_007: Empty email field
8. TC_REG_008: Empty password field
9. TC_REG_009: Empty confirmation field
10. TC_REG_010: Invalid email format (e.g. notanemail)
11. TC_REG_011: Terms/CGU checkbox not accepted (if present)
12. TC_REG_012: All fields empty

Each object must have:
- id: string
- description: string in {lang}
- steps: [{{"field": "name_or_id_or_placeholder", "value": "test data"}}]
- expected: string in {lang}
- verification: {{"url_change": true|false, "error_patterns": ["error text in {lang}"]}}
"""
    fields_json = json.dumps(fields, indent=2)
    human_prompt = f"URL: {url}\nFields detected: {fields_json}"
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    return _parse_json_response(response.content)


def _generate_reset_cases(model, fields, url, lang):
    system_prompt = f"""You are an expert QA Automation Engineer.
Page language: {lang}
Return ONLY a valid JSON array of test case objects. No markdown.

Required test cases:
1. TC_RST_001: Valid password reset request
2. TC_RST_002: Non-existent email
3. TC_RST_003: Empty email field
4. TC_RST_004: Invalid email format

Each object must have:
- id: string
- description: string in {lang}
- steps: [{{"field": "name_or_id_or_placeholder", "value": "test data"}}]
- expected: string in {lang}
- verification: {{"url_change": true|false, "error_patterns": ["error text in {lang}"]}}
"""
    fields_json = json.dumps(fields, indent=2)
    human_prompt = f"URL: {url}\nFields detected: {fields_json}"
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    return _parse_json_response(response.content)


def verify_result(page_text: str, lang: str, expected: dict) -> dict:
    model = get_llm()
    error_patterns = expected.get("error_patterns", [])
    error_patterns_str = ", ".join(f'"{p}"' for p in error_patterns) if error_patterns else ""
    
    text_lower = page_text.lower()
    
    # SPECIAL CASE: Email confirmation pending = SUCCESS for signup
    # Many sites require email verification after signup
    confirm_email_patterns = [
        "check your email", "confirm your email", "verify your email", "confirmer votre email",
        "confirmation email", "verify email", "email confirmation", "activation email",
        "vérifiez votre email", "consulter votre boîte", "email de confirmation",
        "check your inbox", "check email", "verify now", "click the link"
    ]
    if any(pat in text_lower for pat in confirm_email_patterns):
        return {
            "result": "success",
            "error_type": "email_confirmation_pending",
            "confidence": 0.9,
            "reason": "Account created, email confirmation required"
        }

    system_prompt = f"""You are a QA verification expert.
Page language: {lang}

Return ONLY JSON:
{{
  "result": "success" | "failure",
  "error_type": "invalid_credentials" | "email_exists" | "weak_password" | "mismatch" | "required_field" | "generic_error" | "success" | null,
  "confidence": 0.0-1.0,
  "reason": "brief explanation"
}}

Rules:
- If URL changed to dashboard/profile/settings, or welcome/logout/logged-in message visible → "success"
- If page still shows login/signup form, or error message visible → "failure"
- Error types: "required_field", "invalid_credentials", "email_exists", "weak_password", "mismatch"
- Confidence: 0.8-1.0 when clear"""
    human_prompt = f"Page content after submission:\n{page_text[:4000]}\n\nExpected error patterns: [{error_patterns_str}]"
    response = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=human_prompt)])
    raw = response.content.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        text_lower = page_text.lower()
        error_keywords = [
            "invalid", "error", "incorrect", "failed", "wrong", "not found", "denied",
            "invalide", "erreur", "incorrect", "invalido", "incorrecto",
            "erforderlich", "erfordert", "obligatoire", "requis", "vide", "empty",
            "required", "champ", "field"
        ]
        has_error = any(kw in text_lower for kw in error_keywords)
        return {
            "result": "failure" if has_error else "success",
            "error_type": "generic_error" if has_error else "success",
            "confidence": 0.7,
            "reason": "fallback keyword detection"
        }


def _parse_json_response(content: str) -> list:
    raw = content.replace("```json", "").replace("```", "").strip()
    print(f"[DEBUG] LLM raw response length: {len(raw)}")
    
    # Try parsing first
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "test_cases" in data:
            return data["test_cases"]
        return [data]
    except json.JSONDecodeError as e:
        print(f"[DEBUG] JSON decode error: {e}")
    
    # Try to fix common JSON issues
    import re
    
    # Try to extract just the array portion
    match = re.search(r'\[.*\]', raw, re.DOTALL)
    if match:
        fixed = match.group(0)
        try:
            data = json.loads(fixed)
            print(f"[DEBUG] Fixed JSON by extracting array")
            return data if isinstance(data, list) else [data]
        except:
            pass
    
    # Try to parse each test case individually
    test_cases = []
    tc_matches = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', raw)
    for tc_str in tc_matches:
        if '"id"' in tc_str and ('"steps"' in tc_str or '"expected"' in tc_str):
            try:
                tc = json.loads(tc_str)
                if "id" in tc:
                    test_cases.append(tc)
            except:
                continue
    
    if test_cases:
        print(f"[DEBUG] Extracted {len(test_cases)} test cases individually")
        return test_cases
    
    print(f"[DEBUG] Failed raw: {raw[:300]}")
    return []