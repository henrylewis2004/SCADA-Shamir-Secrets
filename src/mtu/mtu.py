import socket
import json
import time
import os

from pymodbus.client import ModbusTcpClient

import crypt 
from nodes import load_nodes

nodes = load_nodes(os.environ.get("NODE_LIST_PATH"))

def make_message(target,function,modbus_address,modbus_value):
    return crypt.message(target,function,modbus_address,modbus_value,crypt.new_nonce(),time.time(),encode=False)

def message_authorised(msg, host, control_port, timeout=5.0):
    key = None
    try:
        shares = crypt.collect_shares(nodes)
        key = bytearray(crypt.recover_key(shares)) #maybe look at collecting own share first
        sig_hex = crypt.sign(key, msg.encode())

    except Exception as e:
        print(f"authorise key & hex generation failure, exception: {e}")
        return False

    finally:
        if key is not None:
            crypt.zeroise(key)

    payload = json.dumps({"msg": msg, "sig": sig_hex}).encode() + b"\n"

    try:
        with socket.create_connection((host, control_port), timeout=timeout) as s:
            s.sendall(payload)
            response = s.recv(4096)
        return response.strip() == b"AUTHORIZED"

    except OSError as e:
        print(f"control channel unreachable: {e}")
        return False


def send_message(message, host, control_port, timeout=5.0):
    if not message_authorised(message,host,control_port,): 
        print(f"failed to authorise message")
        return False

    client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
    client.connect()
    response = client.write_register(address, value, device_id=1)
    client.close()

    return not response.isError()
