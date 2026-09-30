import socket
import json
import time
import os

from pymodbus.client import ModbusTcpClient

import crypt 
from nodes import load_nodes

nodes = load_nodes(os.environ.get("NODE_LIST_PATH"))
field_devices = load_nodes(os.environ.get("FIELD_DEVICE_LIST_PATH"))

def make_message(target,function,modbus_address,modbus_value):
    return crypt.message(target,function,modbus_address,modbus_value,crypt.new_nonce(),time.time(),encode=False)

def message_authorised(msg, host, control_port, timeout=5.0):
    key = None
    try:
       # print("\nkey reconstruction begins!")

        shares = crypt.collect_shares(nodes)
       # print(f"shares: count: {len(shares)}")
        key = bytearray(crypt.recover_key(shares)) #maybe look at collecting own share first
       # print(f"key: {int.from_bytes(key,"big")}, bytes: {key}")
        sig_hex = crypt.sign(key, msg.encode())
        #print("sig_hex made\n")

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


def send_message(message, host, control_port, modbus_port, address, value, timeout=5.0):
    if not message_authorised(message,host,control_port): 
        print(f"failed to authorise message")
        return False

    client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
    client.connect()
    response = client.write_register(address, value, device_id=1)
    print(response)
    client.close()

    return not response.isError()

##
def test_run():
    print("\n\n---starting test run---\n")

    target = os.environ.get("TEST_TARGET")
    host = field_devices[target]["host"]
    control_port = field_devices[target]["control_port"] #int(os.environ.get("TEST_CONTROL_PORT", "6000"))
    modbus_port = field_devices[target]["modbus_port"] #int(os.environ.get("TEST_MODBUS_PORT", "5020"))
    address = 10
    value = 42

    print(f"--- 1) legitimate command: target={target} addr={address} value={value} ---")
    msg = make_message(target, "write_register", address, value)
    ok = send_message(msg, host, control_port, modbus_port, address, value)
    print(f"result: {ok}\n",flush=True)

    print(f"--- 2) wrong target (should be rejected) ---")
    msg = make_message("not_a_real_plc", "write_register", address, value)
    ok = send_message(msg, host, control_port, modbus_port, address, value)
    print(f"result: {ok}\n",flush=True)

    print(f"--- 3) mismatched address/value between signed message and actual write (should be rejected) ---")
    msg = make_message(target, "write_register", address, value)
    ok = send_message(msg, host, control_port, modbus_port, address, 9999)  # different value than what was signed
    print(f"result: {ok}\n",flush=True)


if __name__ == "__main__":
    test_run()

