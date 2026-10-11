from abc import ABC, abstractmethod
from loguru import logger
from pathlib import Path
import aiofiles
import asyncio
import json
import csv
import io

data = {"name": "Abdullah", "age": 21}


class SaveToFile(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def open_file(self, path: str) -> bool:
        pass

    @abstractmethod
    async def save_data(self, data):
        pass

    @abstractmethod
    async def close_file(self):
        pass


class SaveToJSON(SaveToFile):
    def __init__(self):
        self.file = None
        self.is_file_open = False
        self.path = None

    async def open_file(self, path: str) -> bool:
        if not path:
            logger.warning("[JSON FAIL TO SAVE ] Invalid Path")
            return False
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.file = aiofiles.open(self.path, mode="w")
        self.is_file_open = True
        self.file = await self.file.__aenter__()
        return True

    async def save_data(self, data):
        if not data:
            return False
        try:
            json_data = json.dumps(data) + "\n"
            await self.file.write(json_data)
            logger.info(f"[JSON DATA SAVED] PATH {self.path}")
            return True
        except Exception as e:
            await self.file.__aexit__(None, None, None)
            self.is_file_open = False
            logger.warning(f"[JSON DATA FAILED TO SAVE] PATH {self.path}")
            return False

    async def close_file(self):
        if self.is_file_open:
            await self.file.close()
            self.is_file_open = False
            logger.info(f"[JSON FILE CLOSED] PATH {self.path}")
            return True
        return False


class SaveTOCSV(SaveToFile):
    def __init__(self):
        self.file = None
        self.is_file_open = False
        self.path = None
        self.headers_written = False
        self.fieldnames = None

    async def open_file(self, path: str) -> bool:
        if not path:
            logger.warning("[CSV FAIL TO SAVE] Invalid Path")
            return False
        self.path = path
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.file = aiofiles.open(self.path, mode="w", newline="", encoding="utf-8")
        self.file = await self.file.__aenter__()
        self.is_file_open = True
        self.headers_written = False
        return True

    async def save_data(self, data):
        if not data or not self.is_file_open:
            return False
        try:
            buffer = io.StringIO()
            if not self.headers_written:
                self.fieldnames = list(data.keys())
                writer = csv.DictWriter(buffer, fieldnames=self.fieldnames)
                writer.writeheader()
                self.headers_written = True
            else:
                writer = csv.DictWriter(buffer, fieldnames=self.fieldnames)
            writer.writerow(data)
            csv_text = buffer.getvalue()
            await self.file.write(csv_text)
            logger.info(f"[CSV DATA SAVED] PATH {self.path}")
            return True
        except Exception as e:
            logger.warning(f"[CSV DATA FAILED TO SAVE] PATH {self.path} | Error: {e}")
            return False

    async def close_file(self):
        if self.file and self.is_file_open:
            await self.file.close()
            self.is_file_open = False
            logger.info(f"[CSV FILE CLOSED] PATH {self.path}")
            return True
        return False


class StorageContext:
    def __init__(self, strategy: SaveToFile = None):
        self._strategy = strategy

    def set_strategy(self, strategy: SaveToFile):
        """Runtime par strategy change karne ke liye"""
        self._strategy = strategy

    async def open_file(self, path: str) -> bool:
        if not self._strategy:
            logger.error("[STORAGE CONTEXT] No storage strategy set!")
            return False
        return await self._strategy.open_file(path)

    async def save_data(self, data) -> bool:
        if not self._strategy:
            logger.error("[STORAGE CONTEXT] No storage strategy set!")
            return False
        return await self._strategy.save_data(data)

    async def close_file(self) -> bool:
        if not self._strategy:
            return False
        return await self._strategy.close_file()


json_strategy = SaveToJSON()
csv_strategy = SaveTOCSV()
