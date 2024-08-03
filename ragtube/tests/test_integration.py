import json
import unittest
from unittest import TestCase

from chalice.test import Client

from ragtube.app import app


class Test(TestCase):
    def test_index(self):
        with Client(app) as client:
            result = client.http.post("/ping")
            self.assertEqual(result.status_code, 200)
            self.assertEqual(result.body, b'pong')

    def test_handler(self):
        with Client(app) as client:
            message_bodies = [json.dumps({"url": "https://www.youtube.com/watch?v=lPrjP4A_X4s"})]
            result = client.lambda_.invoke(
                "handler",
                client.events.generate_sqs_event(message_bodies, 'ingest-video')
            )

    def test_ask(self):
        with Client(app) as client:
            result = client.http.post("/ask",
                                      headers={"Content-Type": "application/json"},
                                      body=json.dumps({"question": "Why should we rethink exercise?"}))
            print(result.body)


if __name__ == '__main__':
    unittest.main()
