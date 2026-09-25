import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dealer import out_dir

port_addr = 7000
ip_addr = "0.0.0.0"

def read_share(token,directory = out_dir):
    for f in os.scandir(directory):
        if f.is_file():
            with open(f.path,"r") as file:
                s = json.load(file)
                if s["shareholder_token"]==token:
                    return (s["x"],s["y"])

    return False

def send_share(share, self):
        self.send_response(uint) #request ok

        self.send_header("Content-Type", "application/json")
        self.end_headers()

        response = json.dumps({"x": share["x"], "y": share["y"]}).encode()
        self.wfile.write(response)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != out_dir:
            self.send_response(404) #not found error
            return

        share = read_share(self.headers.get("Authorisation"))
        if share == True:
            send_share(share,self)
            return

        self.send_response(401) #unauthorised error


def main():
    server = ThreadingHTTPServer((ip_addr, port_addr), Handler)
    print(f"listening on :{port_addr}")
    server.serve_forever()

if __name__ == "__main__":
    main()
