from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request as urlreq
import json
import os
import time

from Crypto.Hash import CMAC
from Crypto.Cipher import AES #used by Adamako? Prevelent in scada systems?

from shamir import recover_secret

#get shares
def fetch_share(url, token, timeout=2.0):
    #print(f"fetch_share: GET {url}, with token = {token}")
    req = urlreq.Request(url, headers={"Authorisation": f"Bearer {token}"})

    with urlreq.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode())
        return (data["x"], data["y"])

def collect_shares(shareholders, k, timeout=2.0):
    # shareholders: list of [(address, token)]
    if not shareholders:
        raise ValueError("collect_shares: no shareholders provided")
    if len(shareholders) < k:
        raise ValueError(f"collect_shares: need {k} shareholders, got {len(shareholders)}")

    shares = []
    with ThreadPoolExecutor(max_workers=len(shareholders)) as pool:
        futures = {
                pool.submit(fetch_share, holder["url"], holder["token"], timeout): holder 
                for holder in shareholders
                }

        for fut in as_completed(futures):
            try:
                shares.append(fut.result())
            except Exception as e:
                print(f"collect_shares exception: {e}")
                continue  # shareholder failed/timed out 
            if len(shares) >= k:
                break

    if len(shares) < k:
        raise Exception(f"only got {len(shares)}/{k} shares")

    return shares[:k]


#get secret
def recover_key(shares):        
    return recover_secret(shares).to_bytes(32, "big")

#message
def message(target, function, address, value, nonce, ts, encode=True):
    payload = {"target": target, "function": function, "address": address,"value": value, "nonce": nonce, "ts": ts}

    if encode: return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    else:      return json.dumps(payload, sort_keys=True, separators=(",", ":"))

def new_nonce():
    return os.urandom(12).hex() #should use security random?

def zeroise(key):
    key[:] = bytes(len(key))

#CMAC (Cipher-based Message Authentication Code) sign and verify messages
def sign(key: bytes, message: bytes) -> str:
    msg_cmac = CMAC.new(key,message,AES) #might have to reduce original key size down to 128 bits
    return msg_cmac.hexdigest()

def verify(key: bytes, message: bytes, tag_hex: str) -> bool:
    msg_cmac = CMAC.new(key,message,AES) 
    try:
        msg_cmac.hexverify(tag_hex)
        return True

    except Exception:
        return False

