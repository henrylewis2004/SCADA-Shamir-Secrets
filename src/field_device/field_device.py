import socket
import threading
import json
import time
import os

from pymodbus.constants import ExcCodes 
from pymodbus.simulator.simdata import SimData
from pymodbus.simulator.simdevice import SimDevice
from pymodbus.simulator.simutils import DataType
from pymodbus.server import StartTcpServer

import crypt 
from nodes import load_nodes

lock = threading.Lock() #maybe switch to asynclock
seen_nonces = {}     # key: nonce -> value: expiry timestamp
authorised = {}      # key: (address, value) -> value: expiry timestamp
max_nonce_life = 5.0

nodes = load_nodes(os.environ.get("NODE_LIST_PATH"))
k = int(os.environ.get("K_THRESHOLD"))

node_name = os.environ.get("DEVICE_NAME")
ip_addr = os.environ.get("IP_ADDRESS")
control_port = int(os.environ.get("CONTROL_PORT"))
modbus_port = int(os.environ.get("MODBUS_PORT"))

def set_node_name(name="default_name"):
    global node_name
    node_name = name

def fresh_check(nonce,ts):
    if abs(time.time() - ts) > max_nonce_life: return False
    return nonce not in seen_nonces

def nonce_age_check():
    for nonce  in list(seen_nonces):
        if seen_nonces[nonce] < time.time():
            del seen_nonces[nonce]
    for index in list(authorised):
        if authorised[index] < time.time():
            del authorised[index]

def authorise(msg_str, sig_hex):
    time_authorise = time.time()
    payload = json.loads(msg_str)
    address, value, nonce, ts, target = payload["address"], payload["value"], payload["nonce"], payload["ts"], payload["target"]

    if target != node_name: return False

    with lock:
        nonce_age_check()
        if not fresh_check(nonce,ts): return False
        seen_nonces[nonce] = time.time()+max_nonce_life

    key = None
    try:
        shares = crypt.collect_shares(nodes,k)
        key = bytearray(crypt.recover_key(shares)) #maybe look at collecting own share first
        ok = crypt.verify(bytes(key), msg_str.encode(), sig_hex)
    except Exception as e:
        print(f"send command hex generation failure, exception: {e}")
    finally:
        if key is not None:
            crypt.zeroise(key)

    if not ok:
        return False

    with lock:
        authorised[(address,value)] = time.time()+max_nonce_life
    
    time_authorise = time.time() - time_authorise
    print(f"time to authorise: {time_authorise} s", flush=True)
    return True

def serve_one(connection):
    with connection:
        data = b""
        connection.settimeout(5.0)
        while not data.endswith(b"\n"):
            try:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                data += chunk
            except Exception as e:
                print("control channel data connection timeout error:", e)
        try:
            payload = json.loads(data.decode())
            ok = authorise(payload["msg"], payload["sig"])
        except Exception as e:
            print("control channel error:", e)
            ok = False
        connection.sendall(b"AUTHORIZED" if ok else b"DENIED")

def control_channel_server(addr,port):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((addr, port))
    srv.listen(16)
    print(f"control channel listening on :{port}", flush=True)
    while True:
        connection, _ = srv.accept()
        threading.Thread(target=serve_one, args=(connection,), daemon=True).start()


async def gate_action(function_code, start_address, address, count, current_registers, set_values):
 #   time_gate_action = time.time()
    if set_values == None: return None #allows read instructions

    value = set_values[0] if len(set_values)==1 else tuple(set_values)

    with lock:
        if (address, value) not in authorised or authorised[(address,value)] < time.time():
            print(f"address: {address}, value: {value}. not authorised")
            return ExcCodes.NEGATIVE_ACKNOWLEDGE
        del authorised[(address,value)]

 #   time_gate_action = time.time() - time_gate_action
 #   print(f"address: {address}, value: {value}. applied, time: {time_gate_action} s", flush=True)
    return None

def start_modbus_server(addr, port):
    hr_block = SimData(0, count=100, values=0, datatype=DataType.REGISTERS)
    device = SimDevice(id=1, simdata=[hr_block], action=gate_action)
    print(f"Modbus TCP server listening on :{port}",flush=True)
    StartTcpServer(context=device, address=(addr, port))


if __name__ == "__main__":
    threading.Thread(target=control_channel_server, args=(ip_addr,control_port), daemon=True).start()
    start_modbus_server(ip_addr,modbus_port)


