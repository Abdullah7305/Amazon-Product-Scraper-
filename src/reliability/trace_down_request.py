from src.config.project_settings import config
from loguru import logger
from typing import Dict
import time


class CooldownQueueTracker:
    def __init__(self, max_retries: int, cooldown_time: float):
        self.max_retries = max_retries
        self.cooldown_time = cooldown_time
        self.requests: Dict[str, Dict] = {}

    def register_failure(self, request_url: str, reason: str) -> bool:
        current_time = time.time()

        record = self.requests.get(request_url)

        if record is None:
            record = {
                "retries": 0,
                "cooldown_until": 0.0,
                "reason": reason,
                "exhausted": False,
            }
            self.requests[request_url] = record

        record["reason"] = reason

        if record["retries"] >= self.max_retries:
            record["exhausted"] = True
            logger.error(f"[TRACKER] Retries exhausted: {request_url}")
            return False

        record["retries"] += 1

        backoff_delay = (2 ** (record["retries"] - 1)) * self.cooldown_time

        record["cooldown_until"] = current_time + backoff_delay

        logger.warning(
            f"[TRACKER] Retry {record['retries']} scheduled "
            f"for {request_url}; wait={backoff_delay}s; "
            f"reason={reason}"
        )
        return True

    def can_retry_now(self, request_url: str) -> bool:
        record = self.requests.get(request_url)

        if record is None:
            return True

        if record["exhausted"]:
            return False

        return record["cooldown_until"] <= time.time()

    def mark_success(self, request_url: str) -> bool:

        if request_url in self.requests:
            self.requests.pop(request_url, None)
            logger.info(
                f"[TRACKER] URL successfully cleared from tracker: {request_url}"
            )
            return True
        return False

    def get_remaining_cooldown(self, request_url: str) -> float:
        if request_url not in self.requests:
            return 0.0
        remaining = self.requests[request_url]["cooldown_until"] - time.time()
        return max(0.0, remaining)

    def is_exhausted(self, request_url: str) -> bool:
        record = self.requests.get(request_url)
        return bool(record and record["exhausted"])

    def mark_terminal_failure(self, request_url: str, reason: str) -> None:
        record = self.requests.get(request_url)

        if record is None:
            record = {
                "retries": 0,
                "cooldown_until": 0.0,
                "reason": reason,
                "exhausted": True,
            }
            self.requests[request_url] = record
        else:
            record["reason"] = reason
            record["cooldown_until"] = 0.0
            record["exhausted"] = True

        logger.error(f"[TRACKER] Terminal failure: {request_url} | {reason}")


max_retries = int(config.max_retries)
cooldown_time = 12.0
cooldown_queue_tracker = CooldownQueueTracker(
    max_retries=max_retries, cooldown_time=cooldown_time
)
