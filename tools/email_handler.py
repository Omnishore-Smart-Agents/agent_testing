import requests
import time
import re

class EmailHandler:
    def __init__(self):
        self.api_url = "https://www.1secmail.com/api/v1/"
        self.domain = "1secmail.com"

    def generate_email(self):
        """Generate a random email address."""
        ts = int(time.time())
        username = f"qa_test_{ts}"
        return f"{username}@{self.domain}"

    def wait_for_confirmation_link(self, email_address, timeout=60):
        """
        Wait for a new email and extract the first link found in the body.
        Returns the link or None.
        """
        login, domain = email_address.split("@")
        start_time = time.time()
        
        print(f"  ✉️ Waiting for confirmation email on {email_address}...")
        
        while time.time() - start_time < timeout:
            try:
                # 1. Get list of messages
                resp = requests.get(f"{self.api_url}?action=getMessages&login={login}&domain={domain}")
                messages = resp.json()
                
                if messages:
                    msg_id = messages[0]['id']
                    # 2. Read the latest message
                    msg_resp = requests.get(f"{self.api_url}?action=readMessage&login={login}&domain={domain}&id={msg_id}")
                    content = msg_resp.json().get('body', '')
                    
                    # 3. Extract link using regex
                    links = re.findall(r'href=[\'"]?([^\'" >]+)', content)
                    if not links:
                        # Try plain text links
                        links = re.findall(r'(https?://\S+)', content)
                        
                    if links:
                        # Filter out common non-auth links if possible, or just take the first
                        for link in links:
                            if "confirm" in link.lower() or "verify" in link.lower() or "activate" in link.lower() or "supabase" in link.lower():
                                return link
                        return links[0]
                
            except Exception as e:
                print(f"    ⚠️ Error checking email: {e}")
                
            time.sleep(5)
            
        return None
