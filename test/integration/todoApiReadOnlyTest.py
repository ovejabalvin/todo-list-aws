import json
import os
import unittest

import pytest
import requests


BASE_URL = os.environ.get("BASE_URL")
DEFAULT_TIMEOUT = 10


def response_payload(response):
    """Accept both direct API JSON and Lambda proxy bodies serialized as JSON."""
    payload = response.json()
    if isinstance(payload, dict) and isinstance(payload.get("body"), str):
        try:
            return json.loads(payload["body"])
        except json.JSONDecodeError:
            return payload["body"]
    return payload


@pytest.mark.api
class TestApiReadOnly(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(BASE_URL, "BASE_URL no configurada")
        self.assertTrue(len(BASE_URL) > 8, "BASE_URL no configurada")

    def test_api_listtodos_read_only(self):
        print("---------------------------------------")
        print("Starting - production read-only integration test List TODO")
        url = BASE_URL + "/todos"
        response = requests.get(url, timeout=DEFAULT_TIMEOUT)
        print("GET " + url)
        print("Status: " + str(response.status_code))
        print("Body: " + response.text)
        self.assertEqual(response.status_code, 200, "Error en la peticion API")
        payload = response_payload(response)
        self.assertIsNotNone(payload)
        print("Parsed payload: " + str(payload))
        print("End - production read-only integration test List TODO")
