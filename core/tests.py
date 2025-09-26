from django.test import TestCase
import psycopg2
import os

class DatabaseConnectionTest(TestCase):
    def test_database_connection(self):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT"),
            )
            conn.close()
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Database connection failed: {e}")
