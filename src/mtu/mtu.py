import socket
import json
import time
import os

from pymodbus.client import ModbusTcpClient

import crypt 
from nodes import load_nodes
import evaluation

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
    print(f"mtu send message response: {response}",flush=True)
    client.close()

    return not response.isError()

def read_register_address(host, modbus_port, address, timeout=5.0):
    client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
    client.connect()

    response = client.read_holding_registers(address, count=1, device_id=1).registers
    print(f"{host} register {address} value: {response}",flush=True)
    client.close()

    return response


##
def test_run(trial_count=1,target=os.environ.get("TEST_TARGET")):
    print("\n\n---starting test run---\n")

    host = field_devices[target]["host"]
    control_port = field_devices[target]["control_port"] 
    modbus_port = field_devices[target]["modbus_port"] 
    register_address = 10
    value = 42

    trial_res = {}

    res = []
    for i in range(0, trial_count):

        test_name = "legitimate_command"
        print(f"--- 1) {test_name}: target={target} addr={register_address} value={value} ---")
        end_time = time.time()
        msg = make_message(target, "write_register", register_address, value)
        ok = send_message(msg, host, control_port, modbus_port, register_address, value)
        end_time = time.time() - end_time
        response_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {response_value[0]==value}, time: {end_time} s\n",flush=True)
        
        res.append({"correct_result": ok==True, "value_change_correct":response_value[0]==value ,"time": end_time})

    trial_res[test_name]=res

    res=[]
    value = 24
    for i in range(0, trial_count):
        test_name = "wrong_target"
        print(f"--- 2) {test_name} (should be rejected) ---")
        initial_value = read_register_address(host, modbus_port,register_address)
        end_time = time.time()
        msg = make_message("not_a_real_plc", "write_register", register_address, value)
        ok = send_message(msg, host, control_port, modbus_port, register_address, value)
        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time} s\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value,"time": end_time})

    trial_res[test_name]=res

    res=[]
    value = 42
    for i in range(0, trial_count):
        test_name = "mismatched_values"
        print(f"--- 3) {test_name} between signed message and actual write (should be rejected) ---")
        initial_value = read_register_address(host, modbus_port,register_address)
        end_time = time.time()
        msg = make_message(target, "write_register", register_address, value)
        ok = send_message(msg, host, control_port, modbus_port, register_address, 9999)  # different value than what was signed
        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time} s\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    evaluation.mtu_test_run(trial_res)


if __name__ == "__main__":
    test_run(int(os.environ.get("TRIAL_COUNT")))

