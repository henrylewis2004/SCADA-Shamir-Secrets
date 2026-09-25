from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request as urlreq
import json
import os

from Crypto.Hash import CMAC
from Crypto.Cipher import AES #used by Adamako? Prevelent in scada systems?

from shamir import recover_secret

#get shares
def fetch_share(url, token, timeout=2.0):
    req = urlreq.Request(url, headers={"Authorization": f"Bearer {token}"})

    with urlreq.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode())
        return (data["x"], data["y"])

def collect_shares(shareholders, k, timeout=2.0):
    # shareholders: list of {"url":..., "token":...}
    shares = []
    with ThreadPoolExecutor(max_workers=len(shareholders)) as pool:
        futures = {pool.submit(fetch_share, sh["url"], sh["token"], timeout): sh for sh in shareholders}

        for fut in as_completed(futures):
            try:
                shares.append(fut.result())
            except Exception:
                continue  # that shareholder failed/timed out — just skip it
            if len(shares) >= k:
                break

    if len(shares) < k:
        raise Exception(f"only got {len(shares)}/{k} shares")

    return shares[:k]


#get secret
def recover_key(shares):        
    return recover_secret(shares).to_bytes(32, "big")

#message
def message(target, function, address, value, nonce, ts):
    payload = {"target": target, "function": function, "address": address,"value": value, "nonce": nonce, "ts": ts}

    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()

def new_nonce():
    return os.urandom(12).hex() #should use security random?

def zeroize(key_bytes):
    for i in range(len(key_bytes)):
        key_bytes[i] = 0
    return key_bytes


#CMAC (Cipher-based Message Authentication Code) sign and verify messages
def sign(key: bytes, message: bytes) -> str:
    msg_cmac = CMAC.new(key,message,AES) #might have to reduce original key size down to 128 bits
    return msg_cmac.hexdigest()

def verify(key: bytes, message: bytes, tag_hex: str) -> bool:
    msg_cmac = CMAC.new(key,message,AES) #might have to reduce original key size down to 128 bits
    try:
        msg_cmac.hexverify(tag_hex)
        return True

    except Exception:
        return False

