from src.config.project_settings import config
from typing import List, Dict
from loguru import logger
import time


class ProxyManager:
    def __init__(
        self, proxy_list: List[str], cooldown_time: int = 15, failure_count: int = 4
    ):
        logger.info(f"Proxy list created with {len(proxy_list)} proxies.")
        self.proxies: Dict[str, Dict] = {
            proxy: {"failure": 0, "cooldown_until": 0.0} for proxy in proxy_list
        }
        self.max_failures = failure_count
        self.base_cooldown = cooldown_time
        self.current_index = 0

    def report_failure(self, proxy: str):
        if not proxy or proxy not in self.proxies:
            return False

        current_time = time.time()
        self.proxies[proxy]["failure"] += 1
        multiplier = self.proxies[proxy]["failure"]
        cooldown_delay = multiplier * self.base_cooldown
        self.proxies[proxy]["cooldown_until"] = current_time + cooldown_delay

        logger.error(
            f"[PROXY MANAGER] Proxy Failed! {proxy} (Failure count: {multiplier}). "
            f"Cooldown for {cooldown_delay}s"
        )
        return True

    def get_proxy(self) -> str | None:
        if not self.proxies:
            return None

        proxy_keys = list(self.proxies.keys())
        total_proxies = len(proxy_keys)
        current_time = time.time()

        for _ in range(total_proxies):
            candidate = proxy_keys[self.current_index]
            data = self.proxies[candidate]

            self.current_index = (self.current_index + 1) % total_proxies

            if (
                data["cooldown_until"] < current_time
                and data["failure"] < self.max_failures
            ):
                return candidate

        healthy_fallback = min(
            self.proxies.keys(), key=lambda p: self.proxies[p]["cooldown_until"]
        )
        logger.warning(
            f"[PROXY MANAGER] All proxies are on cooldown. Forcing fallback proxy."
        )
        return healthy_fallback

    def report_success(self, proxy: str):
        if not proxy or proxy not in self.proxies:
            return False
        self.proxies[proxy]["failure"] = 0
        self.proxies[proxy]["cooldown_until"] = 0.0
        return True


proxy_list = config.proxy_url_list()
proxy_manager = ProxyManager(proxy_list=proxy_list)
