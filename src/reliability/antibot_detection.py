from bs4 import BeautifulSoup

class AntiBotDetector:
    @staticmethod
    def is_blocked(html_content: str, status_code: int = 200) -> bool:
        if not html_content or status_code in (202, 403, 503, 429):
            return True

        html_lower = html_content.lower()

        # 1. Check for AWS WAF / Goku Challenge scripts
        if "awswafcookiedomainlist" in html_lower or "gokuprops" in html_lower:
            return True

        # 2. Check for truncated responses (Amazon cuts off blocked/throttled streams mid-script)
        if len(html_content) < 5000 or "ue_ibe" in html_lower and not "producttitle" in html_lower:
            return True

        soup = BeautifulSoup(html_content, "lxml")

        # 3. Check root <html> for 'a-no-js' shell wrapper
        html_tag = soup.find("html")
        is_no_js = html_tag and "a-no-js" in html_tag.get("class", [])

        # 4. Product Page Validation: If it's an Amazon product page, it MUST have #productTitle
        has_product_title = soup.select_one("#productTitle") is not None
        if is_no_js or not has_product_title:
            return True

        # 5. Traditional Captcha / Robot Check Titles
        title_tag = soup.title
        title_text = title_tag.string.lower().strip() if (title_tag and title_tag.string) else ""

        if "robot check" in title_text or "amazon.com security check" in title_text:
            return True

        # 6. Captcha Form Selectors
        if soup.select_one("form[action*='validateCaptcha']"):
            return True

        if soup.select_one("input[name='field-keywords']") and soup.select_one("img[src*='captcha']"):
            return True

        if "api-services-support@amazon.com" in html_lower:
            return True

        # 7. Cloudflare / Generic Error indicators
        cf_titles = ["just a moment...", "attention required!", "access denied", "cloudflare"]
        if any(cf in title_text for cf in cf_titles):
            return True

        if soup.select_one("#cf-wrapper, #challenge-running, .cf-browser-verification, #turnstile-wrapper"):
            return True

        if "something went wrong on our end" in html_lower:
            return True

        return False