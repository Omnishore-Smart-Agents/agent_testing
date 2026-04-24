import asyncio
import os

class Executor:
    def __init__(self, browser_wrapper):
        self.browser = browser_wrapper

    async def fill_form(self, form_data: dict) -> dict:
        """
        Fill a form with the given data. form_data is {identifier: value}.
        Returns a dict of results: {identifier: 'ok' | 'failed'}.
        """
        results = {}
        for identifier, value in form_data.items():
            if not value:
                continue
            # Try as regular input first
            success = await self.browser.fill_field(identifier, str(value))
            if not success:
                # Try as select dropdown
                success = await self.browser.select_option(identifier, str(value))
            
            status = "ok" if success else "failed"
            results[identifier] = status
            symbol = "✅" if success else "❌"
            print(f"  {symbol} {identifier} = '{value}' -> {status}")
            await asyncio.sleep(0.3)

        return results

    async def click_submit(self, buttons: list) -> bool:
        """
        Try to click the submit/register button from a list of visible buttons.
        """
        submit_keywords = [
            "submit", "register", "sign up", "create", "join",
            "s'inscrire", "valider", "envoyer", "soumettre", "adhérer",
            "confirmer", "continuer", "continue", "next", "suivant",
            "se connecter", "log in", "login", "connexion", "je me connecte", "sign in"
        ]
        skip_keywords = ["search", "cookie", "accept", "menu", "close", "fermer", "chercher", "annuler", "cancel"]

        best_btn = None
        for btn in buttons:
            text = btn.get("text", "").lower()
            bid = btn.get("id", "").lower()
            bname = btn.get("name", "").lower()
            combined = f"{text} {bid} {bname}"
            
            # Skip buttons that are clearly not submit buttons
            if any(sk in combined for sk in skip_keywords):
                continue
                
            for kw in submit_keywords:
                if kw in combined:
                    best_btn = btn
                    break
            if best_btn: break

        target = best_btn or (buttons[0] if buttons else None)
        if not target:
            return False

        identifier = target.get("id") or target.get("name") or target.get("text")
        print(f"  🖱️ Clicking submit: '{identifier}'")
        
        # Robust click strategy: prioritize actual button elements
        selectors = []
        if target.get("id"): selectors.append(f"#{target['id']}")
        if target.get("name"): selectors.append(f"button[name='{target['name']}'], input[name='{target['name']}']")
        
        # Priority 1: Real button/input tags with this text
        if target.get("text"):
            selectors.append(f"button:has-text('{target['text']}')")
            selectors.append(f"input[value='{target['text']}']")
            selectors.append(f"input[type='submit'][value*='{target['text']}']")
        
        # Priority 2: Any element with this text that has a button role
        if target.get("text"):
            selectors.append(f"[role='button']:has-text('{target['text']}')")
            
        # Last resort: generic text (may hit a header, so we try this last)
        if target.get("text"):
            selectors.append(f"text='{target['text']}'")

        for sel in selectors:
            try:
                success = await self.browser.click_element(sel)
                if success:
                    await asyncio.sleep(1)
                    return True
            except:
                continue
        
        # Final fallback
        return await self.browser.click_element(f"text='{identifier}'")
