import os
import asyncio
import re
from playwright.async_api import async_playwright

# Keywords for detecting registration/login links (multi-language)
REGISTER_KEYWORDS = [
    "sign up", "signup", "register", "create account", "join",
    "s'inscrire", "inscription", "adhérez", "créer un compte",
    "créer compte", "nouveau compte", "enregistrer", "adhérer",
    "create one", "no account", "new user", "get started"
]
LOGIN_KEYWORDS = [
    "sign in", "signin", "log in", "login", "se connecter",
    "connexion", "connecter", "je me connecte"
]


class BrowserWrapper:
    def __init__(self, browser_type: str = "chromium"):
        self.browser_type = browser_type.lower()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_lang = "en"
        self.current_dir = "ltr"

    async def start(self):
        self.playwright = await async_playwright().start()
        
        # Validate browser type
        supported = {"chromium", "chrome", "firefox", "brave"}
        if self.browser_type not in supported:
            print(f"⚠️  Unsupported browser '{self.browser_type}', defaulting to chromium")
            self.browser_type = "chromium"
        
        # Map chrome to chromium
        if self.browser_type == "chrome":
            br￼
owser_launch_type = "chromium"
        else:
            browser_launch_type = self.browser_type
        
        # Brave is Chromium-based, needs special handling
        # Falls back to Chromium if Brave is not installed
        if self.browser_type == "brave":
            import shutil
            brave_executable = (
                shutil.which("brave") or 
                shutil.which("brave-browser") or 
                os.path.expanduser("~/.local/brave/brave/brave") or
                os.path.expanduser("~/.local/brave/brave-browser")
            )
            if brave_executable and os.path.exists(brave_executable):
                self.browser = await self.playwright.chromium.launch(
                    executable_path=brave_executable,
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
                print(f"🚀 Launching Brave browser (via Chromium engine)")
                
                user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Brave/122.0.0.0"
                sec_ua = '"Not A;Brand";v="99", "Brave";v="122"'
                self.context = await self.browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1920, "height": 1080},
                    locale="fr-MA",
                    extra_http_headers={
                        "Accept-Language": "fr-MA,fr;q=0.9,en;q=0.8",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                        "Accept-Encoding": "gzip, deflate, br",
                        "Cache-Control": "no-cache",
                        "Pragma": "no-cache",
                        "Sec-Ch-Ua": sec_ua,
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
                return
            else:
                print(f"⚠️  Brave executable not found, falling back to Chromium")
                browser_launch_type = "chromium"
                self.browser_type = "chromium"
        
        # Standard browser launch for chromium/chrome/firefox
        launch_kwargs = {
            "headless": True,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-web-security",
                "--disable-extensions",
                "--disable-images",
            ]
        }
        
        if browser_launch_type == "firefox":
            launch_kwargs["args"].extend(["--disable-gpu"])
            self.browser = await self.playwright.firefox.launch(**launch_kwargs)
            print(f"🚀 Launching Firefox browser")
        else:
            launch_kwargs["args"].extend([
                "--disable-background-networking",
                "--disable-background-timer-throttling",
            ])
            self.browser = await self.playwright.chromium.launch(**launch_kwargs)
            display_name = "Chrome" if self.browser_type == "chrome" else "Chromium"
            print(f"🚀 Launching {display_name} browser")
        
        # Browser-specific user agents for context
        if self.browser_type == "firefox":
            user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
            sec_ua = '"Not A;Brand";v="99", "Firefox";v="115"'
        elif self.browser_type == "brave":
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Brave/122.0.0.0"
            sec_ua = '"Not A;Brand";v="99", "Brave";v="122"'
        else:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            sec_ua = '"Not A;Brand";v="99", "Chromium";v="122"'
        
        self.context = await self.browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="fr-MA",
            extra_http_headers={
                "Accept-Language": "fr-MA,fr;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Ch-Ua": sec_ua,
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
        await self.page.goto(url, wait_until="networkidle", timeout=60000)
        await self.dismiss_cookie_banners()
        await asyncio.sleep(1)

    async def dismiss_cookie_banners(self):
        cookie_selectors = [
            "button:has-text('Accept All')",
            "button:has-text('Accepter')",
            "button:has-text('Accept')",
            "button:has-text('I Agree')",
            "button:has-text('OK')",
            "#onetrust-accept-btn-handler",
            ".cookie-accept",
            ".accept-cookies"
        ]
        for sel in cookie_selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click(timeout=2000)
                    await asyncio.sleep(1)
                    return
            except Exception:
                pass

    # ── Page Analysis (Python heuristics, no LLM needed) ──

    async def find_links_by_keywords(self, keywords: list) -> list:
        """Find visible <a> links whose text matches any of the keywords."""
        results = []
        links = await self.page.query_selector_all("a:visible")
        for link in links:
            text = (await link.inner_text()).strip().lower()
            for kw in keywords:
                if kw in text:
                    href = await link.get_attribute("href") or ""
                    results.append({"text": (await link.inner_text()).strip(), "href": href, "element": link})
                    break
        return results

    async def find_register_link(self):
        """Find the best registration link on the current page."""
        return await self.find_links_by_keywords(REGISTER_KEYWORDS)

    async def find_login_link(self):
        """Find login link on current page."""
        return await self.find_links_by_keywords(LOGIN_KEYWORDS)

    async def get_form_fields(self) -> list:
        """Extract all visible form fields (inputs, selects, textareas) with metadata."""
        fields = []
        # Text inputs
        inputs = await self.page.query_selector_all("input:not([type='hidden'])")
        for inp in inputs:
            try:
                if not await inp.is_visible():
                    continue
            except:
                continue
            field = {
                "tag": "input",
                "type": await inp.get_attribute("type") or "text",
                "name": await inp.get_attribute("name") or "",
                "id": await inp.get_attribute("id") or "",
                "placeholder": await inp.get_attribute("placeholder") or "",
            }
            # Skip search fields, buttons, and hidden-like inputs
            if field["type"] in ("hidden", "search", "checkbox", "radio", "button", "submit"):
                continue
            # Skip search bar and custom combobox inputs (they have generic ids)
            fid = field["id"].lower()
            if fid in ("q", "search") or fid.startswith("cb"):
                continue
            if field["name"] or field["id"] or field["placeholder"]:
                fields.append(field)

        # Selects
        try:
            selects = await self.page.query_selector_all("select")
            for sel in selects:
                try:
                    if not await sel.is_visible():
                        continue
                    options = await sel.query_selector_all("option")
                    option_values = []
                    for opt in options[:12]:
                        val = await opt.get_attribute("value") or ""
                        text = (await opt.inner_text()).strip()
                        if val and val != "":
                            option_values.append({"value": val, "text": text})
                    fields.append({
                        "tag": "select",
                        "name": await sel.get_attribute("name") or "",
                        "id": await sel.get_attribute("id") or "",
                        "options": option_values
                    })
                except Exception:
                    continue
        except Exception as e:
            print(f"  ⚠️ Warning: Could not extract selects: {e}")

        # Textareas
        textareas = await self.page.query_selector_all("textarea:visible")
        for ta in textareas:
            fields.append({
                "tag": "textarea",
                "name": await ta.get_attribute("name") or "",
                "id": await ta.get_attribute("id") or "",
                "placeholder": await ta.get_attribute("placeholder") or "",
            })

        return fields

    async def get_visible_buttons(self) -> list:
        """Get visible and enabled buttons, excluding common 'cancel' buttons."""
        results = []
        skip_words = ["annuler", "cancel", "fermer", "close", "retour", "back", "reset"]
        
        # Select buttons and inputs that look like buttons
        buttons = await self.page.query_selector_all("button:visible, input[type='submit']:visible, input[type='button']:visible")
        
        for btn in buttons:
            try:
                # Check if disabled
                is_disabled = await btn.evaluate("el => el.disabled || el.classList.contains('disabled') || el.getAttribute('aria-disabled') === 'true'")
                if is_disabled:
                    continue
                
                tag = await btn.evaluate("el => el.tagName.toLowerCase()")
                text = ""
                if tag == "input":
                    text = await btn.get_attribute("value") or ""
                else:
                    text = (await btn.inner_text()).strip()
                
                bid = await btn.get_attribute("id") or ""
                bname = await btn.get_attribute("name") or ""
                
                # Combined check for skip keywords
                full_id = (text + " " + bid + " " + bname).lower()
                if any(sw in full_id for sw in skip_words):
                    continue
                
                if text or bid:
                    results.append({"text": text, "id": bid, "name": bname})
            except Exception:
                continue
        return results

    async def is_captcha_present(self) -> bool:
        """Detect presence of reCAPTCHA or other common captcha iframes."""
        captcha_selectors = [
            "iframe[src*='recaptcha']",
            "iframe[title*='reCAPTCHA']",
            ".g-recaptcha",
            "#captcha",
            ".captcha-container"
        ]
        for sel in captcha_selectors:
            try:
                loc = self.page.locator(sel)
                if await loc.count() > 0:
                    return True
            except:
                pass
        return False

    # ── Actions ──

    async def fill_field(self, identifier: str, value: str):
        """Fill a text field using simulation of real typing for better event triggering."""
        clean = re.sub(r'^(name|id)[\"\':=\s]+', '', identifier, flags=re.IGNORECASE).strip('\'"').strip()
        selectors = [
            f"input[name='{clean}']",
            f"input[id='{clean}']",
            f"#{clean}",
            f"input[placeholder*='{clean}' i]",
            f"textarea[name='{clean}']"
        ]
        for sel in selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    await loc.click() # Focus first
                    await loc.fill("") # Clear
                    await loc.type(value, delay=50) # Type like a human
                    return True
            except Exception:
                continue
        return False

    async def select_option(self, identifier: str, value: str):
        """Select an option in a <select> dropdown by value or label."""
        clean = re.sub(r'^(name|id)[\"\':=\s]+', '', identifier, flags=re.IGNORECASE).strip('\'"').strip()
        selectors = [
            f"select[name='{clean}']",
            f"select[id='{clean}']",
            f"#{clean}",
        ]
        for sel in selectors:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    # 1. Try by value or label exactly
                    try:
                        await loc.select_option(value=value, timeout=1000)
                        return True
                    except:
                        try:
                            await loc.select_option(label=value, timeout=1000)
                            return True
                        except:
                            pass
                    
                    # 2. Smart Fuzzy Match: Look at all options
                    options = await loc.locator("option").all()
                    for opt in options:
                        opt_val = await opt.get_attribute("value") or ""
                        opt_text = (await opt.inner_text()).strip()
                        
                        # Match if value ends with the number (ex: '_02')
                        # or if value is exactly the number
                        # or if text contains the number
                        clean_val = value.zfill(2) # '2' -> '02'
                        if opt_val.endswith(f"_{value}") or opt_val.endswith(f"_{clean_val}") or \
                           value == opt_val or clean_val == opt_val or \
                           value in opt_text:
                            await loc.select_option(value=opt_val, timeout=1000)
                            return True
            except Exception:
                continue
        return False

    async def click_element(self, identifier: str):
        """Click an element by text, id, or selector with force and JS fallback."""
        clean = re.sub(r'^(name|id|text)[\"\':=\s]+', '', identifier, flags=re.IGNORECASE).strip('\'"').strip()
        
        # Strategies to try in order
        strategies = [
            f"#{clean}",
            f"button:has-text(\"{clean}\")",
            f"a:has-text(\"{clean}\")",
            f"input[type='submit'][value*='{clean}']",
            f"text='{clean}'",
            identifier # If it's already a selector
        ]
        
        for sel in strategies:
            try:
                loc = self.page.locator(sel).first
                if await loc.count() > 0:
                    # 1. Try real click with force
                    try:
                        await loc.click(timeout=2000, force=True)
                        return True
                    except:
                        # 2. Try JS fallback
                        await loc.evaluate("el => el.click()")
                        return True
            except Exception:
                continue
        return False

    async def click_link_element(self, link_element):
        """Directly click a Playwright element handle."""
        try:
            await link_element.click(timeout=5000, force=True)
            await self.wait_for_load()
            return True
        except Exception as e:
            print(f"  Click failed: {e}")
            return False

    # ── Utility ──

    async def get_page_url(self):
        return self.page.url

    async def get_page_text(self):
        """Get all visible text on the page for verification."""
        return await self.page.inner_text("body")

    async def wait_for_load(self):
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except:
            pass
        await asyncio.sleep(0.5)

    async def take_screenshot(self, name="screenshot"):
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

    async def has_error_message(self):
<<<<<<< HEAD
        """Check for error messages using error-specific CSS patterns."""
        error_selectors = [
            ".alert-danger", ".alert-error", ".error-message", ".error-msg",
            ".form-error", ".field-error", ".invalid-feedback",
            "[role='alert']", ".notification-error",
            ".portlet-msg-error",  # Liferay-specific
        ]
        for sel in error_selectors:
=======
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
        
        if self.browser_type == "firefox":
            user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
            sec_ua = '"Not A;Brand";v="99", "Firefox";v="115"'
        elif self.browser_type == "brave":
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Brave/122.0.0.0"
            sec_ua = '"Not A;Brand";v="99", "Brave";v="122"'
        else:
            user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            sec_ua = '"Not A;Brand";v="99", "Chromium";v="122"'
        
        try:
            self.context = await self.browser.new_context(
                user_agent=user_agent,
                viewport={"width": 1920, "height": 1080},
                locale="fr-MA",
                extra_http_headers={
                    "Accept-Language": "fr-MA,fr;q=0.9,en;q=0.8",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                    "Sec-Ch-Ua": sec_ua,
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
>>>>>>> feature/souhail
            try:
                loc = self.page.locator(sel)
                if await loc.count() > 0 and await loc.first.is_visible():
                    return True
            except Exception:
                pass
        # Fallback: check for error-like text in prominent elements
        error_keywords = [
            "erreur", "error", "invalide", "invalid", "incorrect", 
            "échoué", "failed", "obligatoire", "required", "manquant",
            "password", "mot de passe", "identifiant"
        ]
        try:
            for sel in ["h1", "h2", "h3", ".alert", ".message", ".notification"]:
                loc = self.page.locator(sel)
                count = await loc.count()
                for i in range(min(count, 5)):
                    text = (await loc.nth(i).inner_text()).lower()
                    if any(kw in text for kw in error_keywords):
                        return True
        except Exception:
            pass
<<<<<<< HEAD
        return False
=======
            self.page = await self.context.new_page()
            try:
                from playwright_stealth import stealth
                await stealth(self.page)
            except Exception:
                pass
        except Exception:
            pass
>>>>>>> feature/souhail

    async def handle_custom_dropdowns(self):
        """Try to interact with custom combobox dropdowns (like Title, Country)."""
        handled = []
        # Find custom combobox-like inputs
        comboboxes = await self.page.query_selector_all("[role='combobox']:visible, input[id^='cb']:visible")
        for cb in comboboxes:
            try:
                cb_id = await cb.get_attribute("id") or ""
                if not cb_id:
                    continue
                # Click to open the dropdown
                await cb.click(timeout=2000)
                await asyncio.sleep(0.5)
                
                # Look for visible options that appeared
                options = await self.page.query_selector_all(f"[role='option']:visible, [id*='{cb_id}'] li:visible, .dropdown-item:visible")
                if options:
                    # Click the first real option (skip empty/placeholder)
                    for opt in options:
                        text = (await opt.inner_text()).strip()
                        if text and text != "--":
                            await opt.click(timeout=2000)
                            handled.append(f"{cb_id} -> '{text}'")
                            await asyncio.sleep(0.3)
                            break
                else:
                    # Click away to close
                    await self.page.click("body")
                    await asyncio.sleep(0.3)
            except Exception as e:
                pass
        return handled

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()