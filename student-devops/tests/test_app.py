import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"app"))
from app import app, validate
import psycopg
class Tests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def test_validation(self):
        self.assertIsNone(validate(None))
        self.assertIsNone(validate({"name":"a","email":"bad","course":"b"}))
        self.assertIsNone(validate({"name":4,"email":"a@b.com","course":"b"}))
        self.assertEqual(validate({"name":" A ","email":"A@B.COM","course":" DevOps "})["email"],"a@b.com")
    def test_live_independent_of_database(self):
        with patch("app.connect", side_effect=AssertionError("Must not query DB")):
            self.assertEqual(self.client.get("/health/live").status_code,200)
    def test_invalid_input(self):
        self.assertEqual(self.client.post("/api/students",json={}).status_code,400)
    def test_database_outage(self):
        with patch("app.connect",side_effect=psycopg.OperationalError("unavailable")):
            self.assertEqual(self.client.get("/health/ready").status_code,503)
    def test_page(self): self.assertEqual(self.client.get("/").status_code,200)
if __name__=="__main__": unittest.main()
