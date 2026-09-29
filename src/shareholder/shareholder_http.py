import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

port_addr = int(os.environ.get("PORT","7000"))
ip_addr = "0.0.0.0"

def read_share():
    with open(os.environ.get("SHARE_PATH")) as file:
        share = json.load(file)

        return share["x"], share["y"], share["shareholder_token"]

share_x, share_y, share_token = read_share() #note may crash if missing file

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != os.environ.get("EXPORT_SHARE_PATH"):
            self.send_response(404) #not found error
            self.end_headers()
            return

        if self.headers.get("Authorization") == f"Bearer {share_token}":
            send_share(self)
            return

        self.send_response(401) #unauthorised error
        self.end_headers()

    def send_share(self):
            self.send_response(200) #request ok

            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = json.dumps({"x": share_x, "y": share_y}).encode()
            self.wfile.write(response)


def main():
    server = ThreadingHTTPServer((ip_addr, port_addr), Handler)
    print(f"listening on :{port_addr}")
    server.serve_forever()

if __name__ == "__main__":
    main()
