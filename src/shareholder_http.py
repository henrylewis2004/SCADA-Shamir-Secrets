import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dealer import shares_dir

port_addr = 7000
ip_addr = "0.0.0.0"

global share_x = None
global share_y = None
global share_token = None

read_share()

def read_share():
    with open(os.environ.get(shares_dir,"share.json")) as file:
        share = json.load(file)

        share_x = share["x"]
        share_y = share["y"]
        share_token = share["shareholder_token"]

def send_share(self):
        self.send_response(200) #request ok

        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = json.dumps({"x": share_x, "y": share_y).encode()
        self.wfile.write(response)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != out_dir:
            self.send_response(404) #not found error
            self.end_headers()
            return

        if self.headers.get("Authorization") == f"Bearer {share_token}"
            send_share(self)
            return

        self.send_response(401) #unauthorised error
            self.end_headers()


def main():
    server = ThreadingHTTPServer((ip_addr, port_addr), Handler)
    print(f"listening on :{port_addr}")
    server.serve_forever()

if __name__ == "__main__":
    main()
