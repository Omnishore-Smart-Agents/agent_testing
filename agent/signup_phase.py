import uuid
import asyncio
from tools.llm import generate_valid_signup_data, verify_result


class SignupPhase:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def run(self, login_url: str, login_fields: list, login_page_info: dict) -> dict | None:
        # If current URL looks like a signup/register page, use it directly
        signup_indicators = ["register", "signup", "sign-up", "inscription", "create-account", "createaccount"]
        current_url_lower = login_url.lower()
        if any(ind in current_url_lower for ind in signup_indicators):
            print(f"📝 [SIGNUP] Already on signup page: {login_url}")
            signup_url = login_url
        else:
            print(f"📝 [SIGNUP] Searching for inscription link on {login_url}")
            signup_url = await self.browser.find_signup_link()
    
            if not signup_url:
                print("📝 [SIGNUP] No inscription link found, trying common paths...")
                signup_url = self._try_common_signup_urls(login_url)

        if not signup_url:
            print("📝 [SIGNUP] Could not find signup page")
            return None

        print(f"📝 [SIGNUP] Navigating to: {signup_url}")
        try:
            await self.browser.page.goto(signup_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            try:
                await self.browser.page.click("#onetrust-accept-btn-handler", timeout=2000)
            except:
                pass
        except Exception as e:
            print(f"📝 [SIGNUP] Could not navigate: {e}")
            return None

        signup_fields = await self.browser.extract_inputs()
        if not signup_fields:
            print("📝 [SIGNUP] No fields found on signup page")
            return None

        signup_page_info = {
            "language": login_page_info.get("language", "en"),
            "direction": login_page_info.get("direction", "ltr"),
            "form_type": "signup",
            "labels": login_page_info.get("labels", {}),
        }

        print(f"📝 [SIGNUP] Found {len(signup_fields)} fields on signup page")
        return await self._create_account(signup_url, signup_fields, signup_page_info)

    def _try_common_signup_urls(self, base_url: str) -> str | None:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        paths = [
            "/fr/inscription",
            "/fr/register",
            "/fr/create-account",
            "/fr/signup",
            "/inscription",
            "/register",
            "/signup",
            "/en/register",
            "/fr/account/register",
            "/fr/user/register",
            "/register.htm",
            "/signup.htm",
            "/create-account",
        ]
        paths_fixed = []
        for path in paths:
            candidate = f"{base}{path}"
            if candidate != base_url and candidate not in paths_fixed:
                paths_fixed.append(candidate)
                return candidate
        return None

    async def _create_account(self, url: str, fields: list, page_info: dict) -> dict | None:
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts:
            attempt += 1
            print(f"📝 [SIGNUP] Attempt {attempt}/{max_attempts}")
            
            signup_data = generate_valid_signup_data(fields, url, page_info)
            if not signup_data:
                print(f"📝 [SIGNUP] Could not generate signup data")
                return None

            email = signup_data.get("email", f"test_{uuid.uuid4().hex[:8]}@example.com")
            password = signup_data.get("password", f"T3st!@{uuid.uuid4().hex[:6]}")
            firstname = signup_data.get("firstname", "Jean")
            lastname = signup_data.get("lastname", "Dupont")
            phone = signup_data.get("phone", "+33612345678")
            country = signup_data.get("country", "FR")
            city = signup_data.get("city", "Paris")
            zipcode = signup_data.get("zip", "75001")
            address = signup_data.get("address", "123 Rue de la Paix")
            birthdate = signup_data.get("birthdate", "15/06/1990")
            gender = signup_data.get("gender", "M")
            terms = signup_data.get("terms", True)
            newsletter = signup_data.get("newsletter", False)
            steps = signup_data.get("fields", [])

            result = {
                "email": email,
                "password": password,
                "signup_url": url,
                "screenshots": [],
            }
            
            print(f"📝 [SIGNUP] Email: {email}")
            print(f"📝 [SIGNUP] Name: {firstname} {lastname}")
            print(f"📝 [SIGNUP] Phone: {phone}")
            print(f"📝 [SIGNUP] Country: {country}")
            print(f"📝 [SIGNUP] City: {city}")
            print(f"📝 [SIGNUP] Address: {address}, {zipcode}")

            # Screenshot before filling
            ss_before = await self.browser.take_screenshot("signup_before_fill")
            result["screenshots"].append({"label": "signup_before_fill", "path": ss_before})

            detected_field_ids = set()
            for f in fields:
                if f.get("id"):
                    detected_field_ids.add(f["id"].lower())
                if f.get("name"):
                    detected_field_ids.add(f["name"].lower())
                if f.get("placeholder"):
                    detected_field_ids.add(f["placeholder"].lower())
                if f.get("label"):
                    detected_field_ids.add(f["label"].lower())

            skip_keywords = {
                "submit", "login", "sign in", "register", "submit button",
                "se connecter", "connexion", "s'inscrire", "sign up", "button",
                "login_button", "submit_button", "btn", "inscription",
                "submit", "envoyer", "valider"
            }

            for f in fields:
                field_type = f.get("type", "").lower()
                field_id = (f.get("id") or "").lower()
                field_name = (f.get("name") or "").lower()
                field_placeholder = (f.get("placeholder") or "").lower()
                field_label = (f.get("label") or "").lower()
                
                if field_type in ("submit", "button"):
                    continue
                if field_type in ("hidden",):
                    continue
                
                value = None
                
                for step in steps:
                    step_field = step.get("field", "").lower()
                    if step_field in field_id or step_field in field_name or step_field in field_placeholder:
                        value = step.get("value")
                        break
                
                if not value:
                    combined = f"{field_id} {field_name} {field_placeholder} {field_label}"
                    
                    if any(kw in combined for kw in ["email", "e-mail", "mail"]):
                        value = email
                    elif any(kw in combined for kw in ["password", "pass", "motdepasse", "mot_de_passe", "pwd"]):
                        value = password
                    elif any(kw in combined for kw in ["firstname", "first_name", "prenom", "prénom", "fname"]):
                        value = firstname
                    elif any(kw in combined for kw in ["lastname", "last_name", "nom", "lname", "family"]):
                        value = lastname
                    elif any(kw in combined for kw in ["phone", "tel", "mobile", "téléphone", "numéro", "phone-number"]):
                        value = phone
                    elif any(kw in combined for kw in ["country", "pays", "pays_id"]):
                        value = country
                    elif any(kw in combined for kw in ["city", "ville", "town", "locality"]):
                        value = city
                    elif any(kw in combined for kw in ["zip", "postal", "code_postal", "zipcode", "code_postal"]):
                        value = zipcode
                    elif any(kw in combined for kw in ["address", "adresse", "street", "adresse_rue"]):
                        value = address
                    elif any(kw in combined for kw in ["birthdate", "birthday", "date_naissance", "dob", "dateOfBirth"]):
                        value = birthdate
                    elif any(kw in combined for kw in ["gender", "genre", "civilité", "civilite", "sex"]):
                        value = gender
                
                if value:
                    try:
                        field_id = f.get("id") or f.get("name") or f.get("placeholder", "")
                        if field_type in ("checkbox",):
                            if value in (True, "true", "1", "on"):
                                await self.browser.page.check(field_id)
                                print(f"  📝 Checked: {field_id}")
                        else:
                            await self.browser.fill_field(field_identifier=field_id, value=value)
                            print(f"  📝 Filled: {field_id} = {value[:20]}...")
                    except Exception as e:
                        pass

            # Screenshot after filling
            ss_filled = await self.browser.take_screenshot("signup_after_fill")
            result["screenshots"].append({"label": "signup_after_fill", "path": ss_filled})

            # Handle checkboxes that need to be checked (terms, newsletter)
            for f in fields:
                field_type = f.get("type", "").lower()
                field_id = (f.get("id") or "").lower()
                field_name = (f.get("name") or "").lower()
                field_label = (f.get("label") or "").lower()
                
                if field_type != "checkbox":
                    continue
                
                combined = f"{field_id} {field_name} {field_label}"
                
                should_check = False
                if any(kw in combined for kw in ["terms", "cgu", "conditions", "accept"]):
                    should_check = terms
                elif any(kw in combined for kw in ["newsletter", "offers", "promotions"]):
                    should_check = newsletter
                
                if should_check:
                    try:
                        field_selector = f.get("id") or f.get("name")
                        if field_selector:
                            await self.browser.page.check(field_selector)
                            print(f"  📝 Checked checkbox: {field_selector}")
                    except Exception as e:
                        pass

            for step in steps:
                field_id = step.get("field", "").strip()
                field_lower = field_id.lower()
                if field_lower in skip_keywords or not field_id:
                    continue
                if field_lower not in detected_field_ids and not any(
                    field_lower in fid for fid in detected_field_ids
                ):
                    continue
                value = step.get("value", "")
                try:
                    await self.browser.fill_field(field_identifier=field_id, value=value)
                    print(f"  📝 Filled: {field_id}")
                except Exception as e:
                    print(f"  ⚠️ Could not fill {field_id}: {e}")

            try:
                await self.browser.click_submit(lang=page_info.get("language", "fr"))
            except Exception as e:
                print(f"❌ [SIGNUP] Could not click submit: {e}")
                continue

            await asyncio.sleep(3)
            page_text = await self.browser.get_page_text()
            lang = page_info.get("language", "fr")
            
            # Screenshot after submit
            ss_after = await self.browser.take_screenshot("signup_after_submit")
            result["screenshots"].append({"label": "signup_after_submit", "path": ss_after})
            
            result = verify_result(page_text, lang, {"url_change": True, "error_patterns": []})

            if result["result"] == "success":
                return {
                    "email": email,
                    "password": password,
                    "signup_url": url,
                    "screenshots": result.get("screenshots", []),
                }

            if result["error_type"] in ("email_exists", "email_confirmation_pending"):
                return {
                    "email": email,
                    "password": password,
                    "signup_url": url,
                    "screenshots": result.get("screenshots", []),
                }

            print(f"📝 [SIGNUP] Result: {result.get('reason', 'unknown')} — retrying...")
            try:
                await self.browser.page.reload(wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
            except Exception:
                pass

        print(f"❌ [SIGNUP] Could not create account after {max_attempts} attempts")
        return None