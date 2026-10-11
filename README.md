# 🛒 AI-Powered Amazon Product Scraper & Dashboard

A production-grade, resilient Amazon scraper that intelligently handles anti-bot defenses, extracts structured product data, enriches missing attributes with AI, stores clean records in PostgreSQL, and serves data through a FastAPI backend and a modern React interface.

---

## 🌟 Key Features

- **Adaptive Multi-Stage Fetching:** Uses fast standard HTTP requests first. If Amazon triggers a bot challenge or CAPTCHA, it seamlessly switches to an automated **Stealth Headless Browser** fallback.
- **Resilient Reliability Layer:**
  - Dynamic proxy management with automatic cooldowns.
  - Exponential backoff retry system.
  - Multi-check anti-bot detection (Goku challenge, AWS WAF, CAPTCHA, and structural layout verification).
- **Intelligent Data Parsing & AI Enrichment:**
  - Extracts titles, ASINs, prices, high-res images, star ratings, specifications, and bullet points.
  - Automatically identifies missing text fields and uses an **LLM (OpenRouter / Gemini / Nemotron)** to enrich product details while keeping ground-truth numeric fields (price, rating) strictly protected.
- **Dual Persistence Pipeline:**
  - Streamed saving to **JSON Lines (`.jsonl`)** and **CSV**.
  - Direct asynchronous insertion into **PostgreSQL** with conflict handling (UPSERT) to prevent duplicate records.
- **Modern Web API & Frontend:**
  - **FastAPI** backend with automated Pydantic schema validation and rate limiting (`slowapi`).
  - **React (TypeScript + Tailwind CSS)** dashboard for single or batch URL scraping with live status feedback.

---

## 🏗️ System Architecture

```text
       [ User / React Frontend ]
                   │
                   ▼  (POST /scrape)
         [ FastAPI Endpoint ]
                   │
                   ▼
     ┌───────── Engine ─────────┐
     │  1. Try Fast HTTP Fetch  │
     │     ├─ Success? ─────────┼──────┐
     │     └─ Blocked?          │      │
     │        ▼                 │      │
     │  2. Stealth Browser      │      │
     │     ├─ Success? ─────────┼──┐   │
     │     └─ Fail ➔ Log Error  │  │   │
     └──────────────────────────┘  │   │
                                   ▼   ▼
                      [ Amazon Product Parser ]
                                   │
                                   ▼  (ProductDetailItem)
                       [ Pipeline Processing ]
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
            [ Cleaner & Dedup ]       [ Check Missing Fields ]
                     │                           │
                     │                 (If fields missing)
                     │                           ▼
                     │                 [ LLM Enrichment API ]
                     │                           │
                     └─────────────┬─────────────┘
                                   │
                     ┌─────────────┴─────────────┐
                     ▼                           ▼
            [ JSONL / CSV File ]       [ PostgreSQL Database ]