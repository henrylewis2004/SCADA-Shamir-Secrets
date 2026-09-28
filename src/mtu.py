import socket
import json
import time

from pymodbus.client import ModbusTcpClient

import crypt 

nodes = []  #same roster-loading gap as plc.py 

#note need to get list of plcs target names
def send_authorise(target, host, control_port, address, value, timeout=5.0):
    msg = crypt.message(target,"write_register",address,value,crypt.new_nonce(),time.time(),encode=False)

    try:
        shares = crypt.collect_shares(nodes)
        key = bytearray(crypt.recover_key(shares)) #maybe look at collecting own share first
        sig_hex = crypt.sign(key, msg)

    except Exception as e:
        print(f"send authorise key & hex generation failure, exception: {e}")
        return False

    finally:
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


def send_message(target, host, control_port, modbus_port, address, value, timeout=5.0):
   if not send_authorise(target,host,control_port,address,value): 
       print(f"failed to authorise message")
       return False

   client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
   client.connect()
   response = client.write_register(address, value, device_id=1)
   client.close()

   return not response.isError()
