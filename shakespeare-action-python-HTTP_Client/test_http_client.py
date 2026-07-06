import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from http_client import http_request


class LocalHTTPHandler(BaseHTTPRequestHandler):
    def _send_text(self, status, body="", headers=None):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.path == "/ok":
            self._send_text(200, "ok")
        elif self.path == "/no-content":
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
        elif self.path == "/echo-header":
            self._send_text(200, self.headers.get("X-Test", ""))
        elif self.path == "/echo-cookie":
            self._send_text(200, self.headers.get("Cookie", ""))
        elif self.path == "/set-cookie":
            self._send_text(200, "set", {"Set-Cookie": "session=abc; Path=/"})
        else:
            self._send_text(404, "not found")

    def do_POST(self):
        self._echo_body()

    def do_PUT(self):
        self._echo_body()

    def do_PATCH(self):
        self._echo_body()

    def do_HEAD(self):
        self._send_text(200)

    def _echo_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        self._send_text(200, f"{self.command}:{body}")

    def log_message(self, *args):
        pass


class HTTPClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), LocalHTTPHandler)
        cls.server_url = f"http://127.0.0.1:{cls.server.server_port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join(timeout=5)

    def request(self, **params):
        base_params = {
            "SERVER": self.server_url,
            "PATH": "/ok",
            "VERIFY_SSL": True,
            "TIMEOUT": 3
        }
        base_params.update(params)
        return http_request(base_params, None, None)

    def test_get_200(self):
        result = self.request()
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["data"]["http_response_code"], 200)
        self.assertEqual(result["data"]["http_response_text"], "ok")

    def test_2xx_status_is_success(self):
        result = self.request(PATH="/no-content")
        self.assertEqual(result["code"], 200)
        self.assertEqual(result["data"]["http_response_code"], 204)
        self.assertIn("成功", result["msg"])

    def test_allow_redirects_accepts_string_false(self):
        result = self.request(PATH="/redirect", ALLOW_REDIRECTS="False")
        self.assertEqual(result["data"]["http_response_code"], 302)

    def test_allow_redirects_accepts_bool_false(self):
        result = self.request(PATH="/redirect", ALLOW_REDIRECTS=False)
        self.assertEqual(result["data"]["http_response_code"], 302)

    def test_header_value_preserves_colons(self):
        result = self.request(
            PATH="/echo-header",
            HEADER="X-Test: Bearer abc:def:ghi"
        )
        self.assertEqual(result["data"]["http_response_text"], "Bearer abc:def:ghi")

    def test_cookie_string_ignores_trailing_semicolon(self):
        result = self.request(
            PATH="/echo-cookie",
            COOKIES="a=1; b=two=2; "
        )
        self.assertEqual(result["code"], 200)
        self.assertIn("a=1", result["data"]["http_response_text"])
        self.assertIn("b=two=2", result["data"]["http_response_text"])

    def test_cookie_file_persists_and_reuses_cookie(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cookie_file = os.path.join(tmpdir, "cookies.txt")
            first = self.request(PATH="/set-cookie", COOKIE_FILE=cookie_file)
            self.assertEqual(first["data"]["http_response_code"], 200)
            self.assertTrue(os.path.exists(cookie_file))

            second = self.request(PATH="/echo-cookie", COOKIE_FILE=cookie_file)
            self.assertIn("session=abc", second["data"]["http_response_text"])

    def test_random_cookie_file_is_created(self):
        result = self.request(COOKIE_FILE="__RANDOM__COOKIE__FILE__")
        cookie_file = result["data"]["cookie_file"]
        try:
            self.assertTrue(os.path.exists(cookie_file))
        finally:
            if cookie_file and os.path.exists(cookie_file):
                os.remove(cookie_file)

    def test_patch_sends_body(self):
        result = self.request(METHOD="PATCH", BODY="hello", PATH="/echo-body")
        self.assertEqual(result["data"]["http_response_text"], "PATCH:hello")

    def test_unsupported_method_returns_error_structure(self):
        result = self.request(METHOD="TRACE")
        self.assertEqual(result["code"], 500)
        self.assertIn("Unsupported HTTP method", result["msg"])
        self.assertEqual(result["data"]["http_response_code"], 0)

    def test_invalid_header_returns_error_structure(self):
        result = self.request(HEADER="BadHeader")
        self.assertEqual(result["code"], 500)
        self.assertIn("Invalid HEADER line", result["msg"])

    def test_missing_server_returns_error_structure(self):
        result = http_request({"PATH": "/"}, None, None)
        self.assertEqual(result["code"], 500)
        self.assertIn("SERVER is required", result["msg"])


if __name__ == "__main__":
    unittest.main()
