import os
import asyncio
from playwright.async_api import async_playwright

SUBMIT_BUTTONS_BY_LANG = {
    "en": ["submit", "login", "sign in", "log in", "log in", "register", "sign up", "create account", "join", "continue"],
    "fr": ["connexion", "se connecter", "s'inscrire", "submit", "valider", "envoyer", "créer un compte", "inscription", "continuer"],
    "ar": ["تسجيل الدخول", "إنشاء حساب", "إرسال", "تسجيل", "دخول", "تسجيل الدخول"],
    "es": ["iniciar sesión", "entrar", "registrarse", "submit", "enviar", "crear cuenta", "continuar"],
    "de": ["anmelden", "einloggen", "registrieren", "submit", "weiter", "konto erstellen"],
    "pt": ["entrar", "iniciar sessão", "registrar", "submit", "criar conta", "continuar"],
    "it": ["accedi", "entra", "registrati", "submit", "crea account", "continua"],
    "zh": ["登录", "提交", "注册", "登陆", "登录", "立即注册"],
    "ja": ["ログイン", "submit", "新規登録", "サインイン", "サインアップ"],
    "ko": ["로그인", "제출", "회원가입", "로그인", "회원 등록"],
    "ru": ["войти", "войти в аккаунт", "зарегистрироваться", "submit", "создать аккаунт"],
    "tr": ["giriş yap", "üye ol", "submit", "kaydol", "hesap oluştur"],
    "nl": ["aanmelden", "inloggen", "registreren", "submit", "doorgaan"],
    "pl": ["zaloguj się", "zarejestruj się", "submit", "utwórz konto", "kontynuuj"],
    "uk": ["увійти", "зареєструватися", "submit", "створити акаунт"],
}


class BrowserWrapper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_lang = "en"
        self.current_dir = "ltr"

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-extensions",
                "--disable-images",
            ]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="fr-MA",
            extra_http_headers={
                "Accept-Language": "fr-MA,fr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Linux"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }
        )
        self.page = await self.context.new_page()
        try:
            from playwright_stealth import stealth
            await stealth(self.page)
        except Exception:
            pass

    async def dismiss_cookies(self):
        try:
            await asyncio.sleep(1)
            selectors = [
                "#onetrust-accept-btn-handler",
                "#onetrust-consent-sdk",
                "button[aria-label='Accept All Cookies']",
                "button:has-text('Accept All')",
                "button:has-text('Allow All')",
                "button:has-text('Tout accepter')",
                "button:has-text('Accepter')",
                ".onetrust-accept-btn-handler",
                "#cookieConsentAccept",
            ]
            for sel in selectors:
                try:
                    count = await self.page.locator(sel).count()
                    if count > 0:
                        for i in range(count):
                            el = self.page.locator(sel).nth(i)
                            try:
                                if await el.is_visible(timeout=1000):
                                    await el.click(timeout=2000)
                                    await asyncio.sleep(0.5)
                                    return True
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception:
            pass
        return False

    async def open_page(self, url: str):
        for attempt in range(5):
            try:
                await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(3)
                title = await self.page.title()
                if "Access Denied" in title or "403" in title or "blocked" in title.lower():
                    if attempt < 4:
                        await asyncio.sleep(5)
                        continue
                return
            except Exception as e:
                if attempt == 4:
                    raise
                await asyncio.sleep(5)

    async def extract_inputs(self):
        fields = []
        selectors = ["input", "select", "textarea"]
        for sel in selectors:
            elements = await self.page.query_selector_all(sel)
            for el in elements:
                atype = await el.get_attribute("type")
                aname = await el.get_attribute("name")
                aid = await el.get_attribute("id")
                aplaceholder = await el.get_attribute("placeholder")
                atag = await el.evaluate("e => e.tagName")
                alabel_text = ""
                field_id = aid or aname or aplaceholder or ""
                if field_id:
                    label_el = await self.page.query_selector(f"label[for='{field_id}']")
                    if label_el:
                        alabel_text = await label_el.inner_text()
                if atag.lower() == "input" and atype in ["hidden", "submit", "button"]:
                    continue
                fields.append({
                    "type": atype or atag.lower(),
                    "name": aname,
                    "id": aid,
                    "placeholder": aplaceholder,
                    "label": alabel_text.strip() if alabel_text else ""
                })
        return fields

    async def detect_language(self) -> tuple[str, str]:
        html_lang = await self.page.get_attribute("html", "lang")
        if html_lang:
            lang = html_lang.split("-")[0].lower()
        else:
            text = await self.page.inner_text("body")
            lang = self._guess_language_from_text(text[:500])
        self.current_lang = lang
        self.current_dir = "rtl" if lang == "ar" else "ltr"
        return lang, self.current_dir

    def _guess_language_from_text(self, text: str) -> str:
        lang_map = {
            "bienvenue": "fr", "connexion": "fr", "s'inscrire": "fr", "mot de passe": "fr",
            "iniciar sesión": "es", "registrarse": "es", "contraseña": "es",
            "anmelden": "de", "registrieren": "de", "passwort": "de",
            "login": "en", "sign in": "en", "password": "en",
            "登录": "zh", "注册": "zh", "登陆": "zh",
            "로그인": "ko", "회원가입": "ko",
            "войти": "ru", "зарегистрироваться": "ru",
            "giriş": "tr", "kaydol": "tr",
            "aanmelden": "nl", "registreren": "nl",
            "zaloguj": "pl", "zarejestruj": "pl",
            "увійти": "uk", "зареєструватися": "uk",
        }
        text_lower = text.lower()
        for keyword, lang in lang_map.items():
            if keyword in text_lower:
                return lang
        return "en"

    async def detect_form_type(self) -> str:
        text = await self.page.inner_text("body")
        text_lower = text.lower()
        signup_keywords = ["sign up", "register", "créer un compte", "s'inscrire", "registrarse", "registrieren", "зарегистрироваться", "注册", "회원가입", "新規登録", "cadastro", "inscription", "crear cuenta", "crea account", "join now"]
        reset_keywords = ["forgot password", "reset", "oublié", "mot de passe oublié", "recuperar contraseña", "recuperar senha", "找回密码", "비밀번호 찾기", "забыли пароль", "şifremi unuttum", "wachtwoord"]
        for kw in signup_keywords:
            if kw in text_lower:
                return "signup"
        for kw in reset_keywords:
            if kw in text_lower:
                return "reset_password"
        return "login"

    async def get_all_buttons(self) -> list[str]:
        buttons = await self.page.query_selector_all("button, input[type='submit'], input[type='button']")
        texts = []
        for btn in buttons:
            text = (await btn.inner_text() or "").strip()
            if text:
                texts.append(text.lower())
            val = await btn.get_attribute("value")
            if val:
                texts.append(val.lower())
        return texts

    async def fill_field(self, field_identifier: str, value: str):
        selectors = [
            f"input[name='{field_identifier}']",
            f"input[id='{field_identifier}']",
            f"input[placeholder*='{field_identifier}']",
            f"#{field_identifier}",
        ]
        for sel in selectors:
            try:
                if await self.page.locator(sel).count() > 0:
                    await self.page.fill(sel, value, timeout=5000)
                    return True
            except Exception:
                continue
        try:
            labels = await self.page.query_selector_all("label")
            for label in labels:
                text = (await label.inner_text() or "").strip().lower()
                if field_identifier.lower() in text:
                    for_attr = await label.get_attribute("for")
                    if for_attr:
                        await self.page.fill(f"#{for_attr}", value, timeout=5000)
                        return True
        except Exception:
            pass
        raise Exception(f"Could not find field: '{field_identifier}'")

    async def click_submit(self, lang: str = "en", form_type: str = "login"):
        submit_texts_by_lang = {
            "en": ["submit", "login", "sign in", "log in", "register", "log in", "continue", "send"],
            "fr": ["connexion", "se connecter", "s'inscrire", "submit", "valider", "envoyer", "continuer", "créer un compte", "inscription"],
            "ar": ["تسجيل الدخول", "إنشاء حساب", "إرسال", "تسجيل"],
            "es": ["iniciar sesión", "entrar", "registrarse", "submit", "enviar", "continuar"],
            "de": ["anmelden", "einloggen", "registrieren", "submit", "weiter"],
            "pt": ["entrar", "iniciar sessão", "registrar", "submit", "continuar"],
            "it": ["accedi", "entra", "registrati", "submit", "continua"],
            "zh": ["登录", "提交", "注册", "登陆", "continuar"],
            "ja": ["ログイン", "submit", "新規登録", "sign in"],
            "ko": ["로그인", "제출", "회원가입"],
            "ru": ["войти", "зарегистрироваться", "submit"],
            "tr": ["giriş yap", "kaydol", "submit", "devam"],
            "nl": ["aanmelden", "registreren", "submit", "doorgaan"],
            "pl": ["zaloguj się", "zarejestruj się", "submit", "kontynuuj"],
            "uk": ["увійти", "зареєструватися", "submit"],
        }
        submit_texts = submit_texts_by_lang.get(lang, submit_texts_by_lang["en"])

        all_btns = await self.page.query_selector_all("button, input[type='submit'], input[type='button']")
        for btn in all_btns:
            try:
                is_visible = await btn.is_visible()
                is_disabled = await btn.get_attribute("disabled")
                if not is_visible or is_disabled is not None:
                    continue
                text = (await btn.inner_text() or "").strip().lower()
                val = (await btn.get_attribute("value") or "").strip().lower()
                for kw in submit_texts:
                    if kw in text or kw in val:
                        await btn.click(timeout=5000)
                        return True
            except Exception:
                continue

        for btn in all_btns:
            try:
                is_visible = await btn.is_visible()
                is_disabled = await btn.get_attribute("disabled")
                if is_visible and is_disabled is None:
                    atype = await btn.get_attribute("type")
                    if atype in ("submit", "button", "") or atype is None:
                        await btn.click(timeout=5000)
                        return True
            except Exception:
                continue

        raise Exception("Submit button not found.")

    async def wait_for_load(self):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass
        await asyncio.sleep(1)

    async def wait_for_post_login(self, original_url: str, timeout: int = 15) -> str:
        """Attend que la page change après login (URL ou contenu dynamique)."""
        success_indicators = [
            "logout", "deconnexion", "se déconnecter", "account", "profil", "profile",
            "welcome", "bienvenue", "dashboard", "mon compte", "my account", "orders",
            "commandes", "settings", "paramètres", "déconnexion", "sign out"
        ]
        for _ in range(timeout):
            await asyncio.sleep(1)
            current = self.page.url
            page_text = (await self.get_page_text() or "").lower()
            page_title = (await self.get_page_title() or "").lower()

            if current != original_url:
                return current
            for indicator in success_indicators:
                if indicator in page_text or indicator in page_title:
                    return current
            if "login" not in current and "sign" not in page_text:
                return current

        return self.page.url

    async def get_page_title(self) -> str:
        try:
            return await self.page.title()
        except Exception:
            return ""

    async def take_screenshot(self, name: str):
        os.makedirs("output/screenshots", exist_ok=True)
        from datetime import datetime
        import time
        ts = int(time.time() * 1000)
        path = f"output/screenshots/{name}_{ts}.png"
        try:
            await self.page.screenshot(path=path, full_page=True, animations="disabled")
            file_size = os.path.getsize(path) if os.path.exists(path) else 0
            print(f"  📸 Screenshot: {path} ({file_size} bytes)")
            return path
        except Exception as e:
            print(f"  📸 Screenshot failed: {e}")
            return None

    async def get_page_content(self):
        return await self.page.content()

    async def get_page_text(self):
        return await self.page.inner_text("body")

    async def get_page_url(self):
        return self.page.url

    async def has_error_message(self):
        try:
            text = await self.get_page_text()
            text_lower = text.lower()
            error_keywords = ["invalid", "error", "incorrect", "failed", "wrong", "not found", "denied", "non trouvé",
                             "invalide", "erreur", "incorrect", "invalido", "incorrecto",
                             "خطأ", "غير صالح", "无效", " ошибка", "geçersiz",
                             "obligatoire", "requis", "required", "vide", "empty", "champ"]
            if any(kw in text_lower for kw in error_keywords):
                return True
            error_elements = await self.page.query_selector_all(
                "[class*='error'], [class*='alert'], [class*='warning'], [role='alert'], .form-error, .field-error, .help-block, .invalid-feedback"
            )
            for el in error_elements:
                try:
                    t = (await el.inner_text() or "").strip()
                    if t:
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    async def reset_session(self):
        try:
            await self.context.close()
        except Exception:
            pass
        try:
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="fr-MA",
                extra_http_headers={
                    "Accept-Language": "fr-MA,fr;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                    "Sec-Ch-Ua-Mobile": "?0",
                    "Sec-Ch-Ua-Platform": '"Linux"',
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            self.page = await self.context.new_page()
            try:
                from playwright_stealth import stealth
                await stealth(self.page)
            except Exception:
                pass
        except Exception:
            pass

    async def find_signup_link(self) -> str | None:
        """Trouve et clique sur un lien d'inscription, retourne l'URL signup."""
        from urllib.parse import urljoin
        base = self.page.url

        signup_keywords = {
            "en": ["sign up", "register", "create account", "join", "signup"],
            "fr": ["inscription", "s'inscrire", "créer un compte", "créer compte", "register", "join"],
            "es": ["registrarse", "crear cuenta", "registro"],
            "ar": ["إنشاء حساب", "تسجيل"],
            "de": ["registrieren", "konto erstellen", "anmelden"],
            "pt": ["registrar", "criar conta", "inscrição"],
            "it": ["registrati", "crea account", "registrazione"],
            "zh": ["注册", "创建账户"],
            "ja": ["新規登録", "登録", "サインアップ"],
            "ko": ["회원가입", "가입"],
        }

        all_links = await self.page.query_selector_all("a")
        for link in all_links:
            try:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text() or "").strip().lower()
                for lang, keywords in signup_keywords.items():
                    for kw in keywords:
                        if kw in text:
                            if href.startswith("http"):
                                return href
                            if href.startswith("/"):
                                return urljoin(base, href)
                            if href.startswith("#") or href.startswith("?"):
                                return urljoin(base, href)
                if "inscription" in href.lower() or "register" in href.lower() or "signup" in href.lower():
                    if href.startswith("http"):
                        return href
                    if href.startswith("/"):
                        return urljoin(base, href)
            except Exception:
                continue

        buttons = await self.page.query_selector_all("button")
        for btn in buttons:
            try:
                text = (await btn.inner_text() or "").strip().lower()
                for lang, keywords in signup_keywords.items():
                    for kw in keywords:
                        if kw in text:
                            try:
                                await btn.click(timeout=2000)
                                await asyncio.sleep(3)
                                return self.page.url
                            except Exception:
                                pass
            except Exception:
                continue

        return None

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()