import os
import dotenv

dotenv.load_dotenv()


class ProjectSettings:

    def __init__(self):

        self.site_name = os.getenv("SITE_NAME")
        self.max_pages = os.getenv("MAX_PAGES")
        self.max_retries = os.getenv("MAX_RETRIES")
        self.request_timeout = os.getenv("REQUEST_TIMEOUT")
        self.concurrent_req_limit = os.getenv("CONCURRENT_REQUESTS")

        self.proxy_host = os.getenv("PROXY_HOST")
        self.proxy_user = os.getenv("PROXY_USER")
        self.proxy_pass = os.getenv("PROXY_PASS")
        self.proxy_port = os.getenv("PROXY_PORT")
        self.proxy_gateway = os.getenv("PROXY_GATEWAY")
        self.proxy_cooldown = os.getenv("PROXY_BASE_COOLDOWN")

        self.output_dir_path = os.getenv("OUTPUT_DIR")

        self.llm_api_key = os.getenv("LLM_API_KEY")

        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_name = os.getenv("DB_NAME")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")

    def proxy_url_list(self) -> list[str]:
        proxies = [
            "http://fngjbuod:n9nyxtrfm63q@31.59.20.176:6754/",
            "http://fngjbuod:n9nyxtrfm63q@45.38.107.97:6014/",
            "http://fngjbuod:n9nyxtrfm63q@64.137.96.74:6641/",
            "http://fngjbuod:n9nyxtrfm63q@198.23.243.226:6361/",
        ]
        # raw_proxies = os.getenv("PROXY_LIST")
        # if not raw_proxies:
        #     return []

        # proxy_items = raw_proxies.split(",")
        # formatted_proxies = []
        # for item in proxy_items:
        #     parts = item.split(":")
        #     if len(parts) == 4:
        #         host, port, username, password = parts
        #         formatted = f"http://{self.proxy_user}:{self.proxy_pass}@{host}:{port}"
        #         formatted_proxies.append(formatted)
        #     elif len(parts) == 2:
        #         host, port = parts
        #         formatted = f"http://{host}:{port}"
        #         formatted_proxies.append(formatted)

        return proxies


config = ProjectSettings()

print(config.db_host)
print(config.db_name)
print(config.db_pass)
print(config.db_pass)