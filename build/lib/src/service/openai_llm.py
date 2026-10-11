import asyncio
import json
from loguru import logger
from openai import AsyncOpenAI
from src.config.project_settings import config


class GeminiLLM:
    def __init__(self, model_name: str = "nvidia/nemotron-3-super-120b-a12b:free"):
        self.api_key = config.llm_api_key
        self.model_name = model_name
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )

    def validate_raw_data(self, item: dict) -> tuple[bool, str]:
        """Fast Python pre-validation check before hitting API rate/cost limits."""
        if not item or not isinstance(item, dict):
            return False, "Data is empty or not a valid dictionary structure."

        title = item.get("title")
        if not title or len(str(title).strip()) < 5:
            return False, "Title is missing or contains fewer than 5 characters."

        return True, "Basic Python validation passed successfully."

    async def process_and_validate_batch(self, items: list[dict]) -> list[dict]:
        """Executes batch pipeline: Fast Pre-checks -> Batch OpenRouter Request -> Strict JSON Array Parsing."""
        if not items or not isinstance(items, list):
            logger.warning(
                "[LLM BATCH] Provided items parameter is empty or not a list."
            )
            return []

        # 1. First-Level Fast Python Pre-Check for each item in batch
        valid_items_for_llm = []
        for item in items:
            is_valid, reason = self.validate_raw_data(item)
            if is_valid:
                valid_items_for_llm.append(item)
            else:
                logger.warning(
                    f"[LLM PRE-CHECK FAILED] ASIN: {item.get('asin', 'N/A')} - Reason: {reason}"
                )

        # If no items passed the Python pre-check, exit early without calling LLM
        if not valid_items_for_llm:
            logger.warning("[LLM BATCH] All items in batch failed Python pre-check.")
            return []

        # 2. JSON-Enforced Batch Prompt Construction
        system_prompt = (
            "You are an expert AI data auditor for e-commerce Web Scraping. "
            "Analyze a list of scraped product items, validate quality, extract key features, "
            "and ALWAYS respond ONLY with a clean JSON Array of objects."
        )

        user_prompt = f"""
Analyze the following batch of scraped product data items.
Return a JSON Array containing an object for EACH item with this exact structure:

[
  {{
    "asin": "Product ASIN",
    "is_valid_product": true/false,
    "confidence_score": 0.0 to 1.0,
    "clean_title": "Extracted main product title",
    "category": "Estimated main category",
    "key_features": ["feature 1", "feature 2"],
    "validation_notes": "Reason if product is invalid or incomplete"
  }}
]

Raw Scraped Data Batch:
{json.dumps(valid_items_for_llm, indent=2)}
"""

        # 3. OpenRouter API Call
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Lower temperature for deterministic output
            )

            raw_content = response.choices[0].message.content.strip()

            # Clean markdown code block wrappers if present in response
            if raw_content.startswith("```json"):
                raw_content = (
                    raw_content.replace("```json", "").replace("```", "").strip()
                )
            elif raw_content.startswith("```"):
                raw_content = raw_content.replace("```", "").strip()

            # 4. Parse Structured Output Array
            parsed_results = json.loads(raw_content)

            if isinstance(parsed_results, list):
                logger.info(
                    f"[LLM BATCH SUCCESS] Successfully processed {len(parsed_results)} items in single API request."
                )
                return parsed_results
            else:
                logger.error(
                    "[LLM PARSE ERROR] Expected a JSON Array from model but received a single object/other type."
                )
                return []

        except json.JSONDecodeError as e:
            logger.error(
                f"[LLM PARSE ERROR] Invalid JSON format received from model: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"[LLM API ERROR] Request failed: {e}")
            return []


async def main():
    logger.info("Initializing GeminiLLM Batch Test Execution...")

    llm_service = GeminiLLM()

    # Batch containing multiple items (Valid + Bad)
    sample_batch = [
        {
            "asin": "B09XS7JLH3",
            "title": "Sony WH-1000XM5 Wireless Noise Canceling Headphones",
            "price": "$398.00",
            "rating": "4.5 out of 5 stars",
            "description": "Auto NC Optimizer, 30-hour battery life.",
        },
        {
            "asin": "B08N5WRWNW",
            "title": "Apple MacBook Air Laptop M1 Chip 13-inch Retina Display",
            "price": "$999.00",
            "rating": "4.8 out of 5 stars",
            "description": "8GB RAM, 256GB SSD Storage, Backlit Keyboard.",
        },
        {
            "asin": "B000000000",
            "title": "",  # Will fail Python pre-check locally
            "price": None,
        },
    ]

    print("\n--- Testing Batch Execution ---")
    results = await llm_service.process_and_validate_batch(sample_batch)
    print("\nProcessed Batch Output Results:")
    print(json.dumps(results, indent=2))


# if __name__ == "__main__":
#     asyncio.run(main())

llm_service = GeminiLLM()
