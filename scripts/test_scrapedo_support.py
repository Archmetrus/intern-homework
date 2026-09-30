"""Gerçek token kullanmadan yerel proxy doğrulaması: python -m unittest discover -s scripts."""

import os
import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import ssl
import subprocess
import threading
import unittest
import io
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from browser_config import configure_browser
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from scrapedo_support import ask_credentials, install_proxy_auth

ROOT = Path(__file__).resolve().parents[1]
DRIVER = os.environ.get('CHROMEDRIVER_PATH') or None


class ScrapedoTests(unittest.TestCase):
    def test_navigation_error_keeps_window_open_and_redacts_details(self):
        import selenium_demo
        from selenium.common.exceptions import WebDriverException
        driver = MagicMock()
        driver.get.side_effect = WebDriverException('net::ERR_PROXY_CONNECTION_FAILED https://example.com/?token=secret-test-token')
        output = io.StringIO()
        with patch('sys.argv', ['demo', '--url', 'https://example.com', '--keep-open']), \
                patch.object(selenium_demo.os.path, 'lexists', return_value=False), \
                patch.object(selenium_demo, 'Service'), \
                patch.object(selenium_demo.webdriver, 'Chrome', return_value=driver), \
                patch('builtins.input', return_value='') as prompt, \
                patch('sys.stdout', output):
            self.assertEqual(selenium_demo.main(), 1)
        prompt.assert_called_once()
        driver.quit.assert_called_once()
        self.assertIn('ERR_PROXY_CONNECTION_FAILED', output.getvalue())
        self.assertIn('Sayfaya bağlanma', output.getvalue())
        self.assertNotIn('secret-test-token', output.getvalue())

    def test_token_not_sent_to_origin_or_another_proxy(self):
        from selenium.webdriver.common.devtools.v152 import fetch
        callbacks, commands = {}, []
        connection = SimpleNamespace(
            add_callback=lambda event, callback: callbacks.update({event: callback}),
            execute=lambda command: commands.append(next(command)),
        )
        driver = SimpleNamespace(start_devtools=lambda: (SimpleNamespace(fetch=fetch), connection))
        install_proxy_auth(driver, 'secret-test-token', 'render=false')
        for source, origin in [('Server', 'https://proxy.scrape.do:8080'), ('Proxy', 'https://elsewhere.invalid:8080')]:
            event = SimpleNamespace(request_id=fetch.RequestId(source),
                                    auth_challenge=SimpleNamespace(source=source, origin=origin))
            callbacks[fetch.AuthRequired](event)
            response = commands[-1]['params']['authChallengeResponse']
            self.assertEqual(response, {'response': 'Default'})

    def test_prompt_retries(self):
        with patch.dict('os.environ', {'SCRAPEDO_TOKEN': ''}), \
                patch('getpass.getpass', side_effect=['', 'test-token']), \
                patch('builtins.input', side_effect=['1000001', 'abc', '42']):
            self.assertEqual(ask_credentials(), ('test-token', 'render=false&sessionId=42'))

    def test_local_authenticated_proxy(self):
        self.check_proxy(False)

    def test_local_https_connect_proxy(self):
        self.check_proxy(True)

    def check_proxy(self, tls):
        seen = []
        expected = 'Basic ' + base64.b64encode(b'test-token:render=false').decode()
        tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

        class Proxy(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_CONNECT(self):
                if not tls:
                    self.send_error(502)
                    return
                auth = self.headers.get('Proxy-Authorization')
                seen.append(auth)
                if auth != expected:
                    self.send_response(407)
                    self.send_header('Proxy-Authenticate', 'Basic realm="local-test"')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                self.send_response(200, 'Connection established')
                self.end_headers()
                self.wfile.flush()
                self.connection.settimeout(5)
                try:
                    with tls_context.wrap_socket(self.connection, server_side=True) as tunnel:
                        headers = b''
                        while b'\r\n\r\n' not in headers and len(headers) < 65536:
                            chunk = tunnel.recv(4096)
                            if not chunk:
                                return
                            headers += chunk
                        body = b'<html><body>proxy-auth-ok</body></html>'
                        tunnel.sendall(b'HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nConnection: close\r\nContent-Length: ' + str(len(body)).encode() + b'\r\n\r\n' + body)
                except (ssl.SSLError, OSError):
                    pass

            def do_GET(self):
                auth = self.headers.get('Proxy-Authorization')
                seen.append(auth)
                if auth != expected:
                    self.send_response(407)
                    self.send_header('Proxy-Authenticate', 'Basic realm="local-test"')
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                    return
                body = b'<html><body>proxy-auth-ok</body></html>'
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        with ThreadingHTTPServer(('127.0.0.1', 0), Proxy) as server:
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with tempfile.TemporaryDirectory(prefix='auth-test-', dir=ROOT) as profile:
                    if tls:
                        cert, key = str(Path(profile) / 'cert.pem'), str(Path(profile) / 'key.pem')
                        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                                        '-keyout', key, '-out', cert, '-days', '1', '-subj', '/CN=homework.invalid'],
                                       capture_output=True, check=True, timeout=15)
                        tls_context.load_cert_chain(cert, key)
                    proxy = f'http://127.0.0.1:{server.server_port}'
                    options = webdriver.ChromeOptions()
                    # Yalnızca geçici yerel testin kendi sertifikası için.
                    options.accept_insecure_certs = tls
                    configure_browser(options)
                    for argument in ['--headless=new', f'--user-data-dir={profile}', f'--proxy-server={proxy}']:
                        options.add_argument(argument)
                    with webdriver.Chrome(service=Service(DRIVER), options=options) as driver:
                        driver.set_page_load_timeout(15)
                        state = install_proxy_auth(driver, 'test-token', 'render=false', proxy)
                        driver.get(('https' if tls else 'http') + '://homework.invalid/')
                        self.assertIn('proxy-auth-ok', driver.page_source)
                        self.assertIn(expected, seen)
                        self.assertFalse(state['rejected'])
                        self.assertFalse(state['callback_failed'])
            finally:
                server.shutdown()
                worker.join(timeout=5)


if __name__ == '__main__':
    unittest.main()
