import json
import os
import secrets

import shamir  

out_dir = './shares'

def make_key():
    return secrets.token_bytes(32) # maybe look into why 32 bytes / 256 bits

def get_key_int(key):
    return int.from_bytes(key,'big')

#writes each share to a file to send to shareholders
#maybe change to send files (add a destination and send it from here)
def make_files(shares,output_directory = out_dir):
    os.makedirs(output_directory, exist_ok=True)

    for (x, y) in shares:
        shareholder_token = secrets.token_hex(16)          
        filename = os.path.join(output_directory, f"shareholder_{x}.json")
        with open(filename, "w") as f:
            json.dump({"x": x, "y": y, "shareholder_token": shareholder_token}, f)

        print(f"shareholder {x}: token={shareholder_token}")   # so you have a record of it


#deals out shares 
def deal(n,k,key=make_key()):
    #print(key)
    #print(get_key_int(key))
    shares = shamir.split_secret(get_key_int(key),n,k)
    make_files(shares)

    print(f"\n{n} shares created with k = {k}\n")

def get_shares(output_directory=out_dir):
    shares = []
    for f in os.scandir(output_directory):
        if f.is_file():
            with open(f.path,"r") as file:
                s = json.load(file)
                shares.append([s["x"],s["y"]])

    return shares


def test():
    n = 5
    k = 3

    deal(n,k)
    shares = get_shares()

    print(shamir.recover_secret(shares))
    print(shamir.recover_secret(shares).to_bytes(32,"big"))


