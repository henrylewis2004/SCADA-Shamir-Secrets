import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from dealer import out_dir

def read_share(token,directory = out_dir):
    for f in os.scandir(directory):
        if f.is_file():
            with open(f.path,"r") as file:
                s = json.load(file)
                if s["shareholder_token"]==token:
                    return (s["x"],s["y"])

    return False

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != out_dir:
            #
            return

