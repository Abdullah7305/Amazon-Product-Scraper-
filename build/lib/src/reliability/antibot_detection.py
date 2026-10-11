from bs4 import BeautifulSoup


class AntiBotDetector:
    @staticmethod
    def is_blocked(html_content: str) -> bool:
        if not html_content:
            return True

        soup = BeautifulSoup(html_content, "lxml")
        title_text = soup.title.string.lower().strip() if soup.title else ""

        if "robot check" in title_text or "amazon.com security check" in title_text:
            return True

        # Amazon Captcha form selector
        if soup.select_one("form[action*='validateCaptcha']"):
            return True

        # Captcha image input field selector
        if soup.select_one("input[name='field-keywords']") and soup.select_one(
            "img[src*='captcha']"
        ):
            return True
        if "api-services-support@amazon.com" in html_content.lower():
            return True

        # 2. Cloudflare Challenge Selectors
        cf_titles = [
            "just a moment...",
            "attention required!",
            "access denied",
            "cloudflare",
        ]
        if any(cf in title_text for cf in cf_titles):
            return True

        # Cloudflare wrapper IDs aur Classes
        if soup.select_one(
            "#cf-wrapper, #challenge-running, .cf-browser-verification, #turnstile-wrapper"
        ):
            return True

        # Cloudflare Turnstile / Challenge Iframe
        if soup.select_one("iframe[src*='cloudflare.com']"):
            return True

        # 3. Generic 503 / Block text indicators
        if "something went wrong on our end" in html_content.lower():
            return True

        return False
