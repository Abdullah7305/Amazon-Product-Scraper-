from src.config.project_settings import config
from typing import Dict, List, Optional
from loguru import logger
import psycopg2
import json


class PostgresDatabase:
    def __init__(self):
        self.connection = None
        self.cursor = None
        self.is_connection = False
        self.table_created = False

    def open(self):
        self.connection = psycopg2.connect(
            host="localhost",
            port=5432,
            database="scraper_db",
            user="postgres",
            password="Abdullah123",
        )
        logger.info("[CONNECTION INITILIZED]")
        self.cursor = self.connection.cursor()
        self.is_connection = True

    def create_table(self):
        if not self.is_connection:
            logger.info("[No Connection WITH DB]")
            return
        if self.table_created:
            logger.info("[TABLE ALREADY CREATED]")
            return
        create_table_query = """
            CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            asin VARCHAR(20) UNIQUE NOT NULL,
            title TEXT NOT NULL,
            brand VARCHAR(255),
            price NUMERIC(10, 2),
            currency VARCHAR(5) DEFAULT '$',
            rating NUMERIC(3, 2),
            review_count INTEGER,
            availability VARCHAR(100),
            product_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.cursor.execute(create_table_query)
        self.table_created = True
        logger.info("[TABLE CREATED SUCCESSFULLY]")

    def save_data(self, items: List[Dict]):
        if not items:
            logger.info("[ITEM MISSING TO INSERT]")
            return

        if not self.is_connection:
            logger.info("[NO DB CONNECTION]")
            return

        if not self.table_created:
            logger.info("[NO TABLE CREATED ]")
            return
        insert_query = """
            INSERT INTO products(asin, title, brand, price, rating, review_count, product_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (asin) DO NOTHING
        """
        values = (
            items["asin"],
            items["title"],
            items["brand"],
            items["price"],
            items["rating"],
            items["review_count"],
            items["product_url"],
        )

        self.cursor.execute(insert_query, values)
        self.connection.commit()
        logger.info("[ITEMS INSERTED TO TABLE SUCCESSFULLY]")

    def get_data(self):
        if not self.is_connection:
            logger.info("[NO DB CONNECTION]")
            return

        if not self.table_created:
            logger.info("[NO TABLE CREATED ]")
            return
        retrieve_query = """
            SELECT * FROM products
        """
        self.cursor.execute(retrieve_query)
        record = self.cursor.fetchall()
        return record

    def close(self):
        if not self.is_connection:
            logger.info("[NO DB CONNECTION]")
            return

        if not self.table_created:
            logger.info("[NO TABLE CREATED ]")
            return

        self.cursor.close()
        self.connection.close()
        logger.info("[DB CONNECTION CLOSED ]")


postgres_db = PostgresDatabase()


def main():
    # products_batch = [
    #     (
    #         "B07D13B3N1",
    #         "Under Armour T-Shirt",
    #         "Under Armour",
    #         25.00,
    #         4.3,
    #         5420,
    #         "https://www.amazon.com/dp/B07D13B3N1",
    #     ),
    #     (
    #         "B08GP72RFX",
    #         "Magicmode Gyroscope",
    #         "Magicmode",
    #         15.99,
    #         4.1,
    #         890,
    #         "https://www.amazon.com/dp/B08GP72RFX",
    #     ),
    # ]
    products_batch = (
        "B07D13B3N1",
        "Under Armour T-Shirt",
        "Under Armour",
        25.00,
        4.3,
        5420,
        "https://www.amazon.com/dp/B07D13B3N1",
    )
    db = PostgresDatabase()
    db.open()
    db.create_table()
    db.save_data(products_batch)
    record = db.get_data()
    print(f"Record: {record}")
    db.close()
