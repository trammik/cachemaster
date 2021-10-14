from http.server import HTTPServer, BaseHTTPRequestHandler
from itertools import cycle
DIFF = cycle(range(-1, -5, -1))


class Handler(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

    def do_GET(self):
        if 'usd' in self.path.lower():
            self._set_headers()
            body = {"USD": 26.45 * (1 + next(DIFF) / 100)}
            self.wfile.write(f'{body}'.encode('utf-8'))
        elif 'eur' in self.path.lower():
            self._set_headers()
            body = {"EUR": 30.25 * (1 + next(DIFF) / 100)}
            self.wfile.write(f'{body}'.encode('utf-8'))


if __name__ == "__main__":
    server_addr = ('localhost', 8888)
    httpd = HTTPServer(server_addr, Handler)
    print(f"Starting http server on {server_addr[0]}:{server_addr[1]}")
    httpd.serve_forever()
