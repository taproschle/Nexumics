import unittest

from nexumics.entrez import EntrezResponse, parse_esearch_history, parse_esearch_ids
from nexumics.raw_storage import redact_params, redact_url


class EntrezTests(unittest.TestCase):
    def test_parse_esearch_ids(self) -> None:
        response = EntrezResponse(
            utility="esearch",
            url="https://example.test",
            params={},
            status_code=200,
            content_type="application/json",
            text='{"esearchresult": {"idlist": ["123", "456"]}}',
        )

        self.assertEqual(parse_esearch_ids(response), ["123", "456"])

    def test_parse_esearch_history(self) -> None:
        response = EntrezResponse(
            utility="esearch",
            url="https://example.test",
            params={},
            status_code=200,
            content_type="application/json",
            text=(
                '{"esearchresult": {'
                '"count": "42", '
                '"querykey": "1", '
                '"webenv": "NCBI_ENV", '
                '"idlist": ["123"]'
                "}}"
            ),
        )

        history = parse_esearch_history(response)

        self.assertEqual(history.count, 42)
        self.assertEqual(history.query_key, "1")
        self.assertEqual(history.webenv, "NCBI_ENV")
        self.assertEqual(history.ids, ["123"])

    def test_redacts_api_key_from_raw_metadata(self) -> None:
        params = {"db": "sra", "api_key": "secret-key"}
        url = "https://example.test/eutils/esearch.fcgi?db=sra&api_key=secret-key"

        self.assertEqual(redact_params(params)["api_key"], "[REDACTED]")
        self.assertIn("api_key=%5BREDACTED%5D", redact_url(url))
        self.assertNotIn("secret-key", redact_url(url))
