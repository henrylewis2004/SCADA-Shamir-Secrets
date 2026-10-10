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

k = int(os.environ.get("K_THRESHOLD"))
n = int(os.environ.get("N_COUNT"))

def make_message(target,function,modbus_address,modbus_value,ts=time.time()):
    make_message_time = time.time()

    msg = crypt.message(target,function,modbus_address,modbus_value,crypt.new_nonce(),ts,encode=False)

    make_message_time = time.time() - make_message_time

    #print(f"time to make message: {end_time*1000} ms")
    return msg, make_message_time

def message_authorised(msg, host, control_port, missing_share_count, timeout=5.0):
    timeset={}
    end_time=time.time()
    key = None

    try:
        share_time = time.time()
        shares = crypt.collect_shares(nodes,k)
        timeset["share_collection"] = time.time() - share_time  

        con_time = time.time()
        key = bytearray(crypt.recover_key(shares[0:len(shares)-missing_share_count])) 
        timeset["key_construction"] = time.time() - con_time

        sign_time = time.time()
        sig_hex = crypt.sign(key, msg.encode())
        timeset["message_signature_time"] = time.time() - sign_time

        timeset["share_cost_total"] = time.time() - share_time    

    except Exception as e:
        print(f"authorise key & hex generation failure, exception: {e}")
        return False, timeset

    finally:
        if key is not None:
            zero_time = time.time()
            crypt.zeroise(key)
            timeset["zeroise_time"] = time.time() - zero_time

    payload = json.dumps({"msg": msg, "sig": sig_hex}).encode() + b"\n"

    try:
        auth_time = time.time()
        with socket.create_connection((host, control_port), timeout=timeout) as s:
            s.sendall(payload)
            response = s.recv(4096)
        timeset["auth_time"] = time.time() - auth_time

        timeset["total_auth_time"] = time.time() - end_time
        return response.strip() == b"AUTHORIZED",timeset

    except OSError as e:
        print(f"control channel unreachable: {e}")
        return False

def send_message(message, host, control_port, modbus_port, address, value, timeout=5.0, missing_share_count=0):
    ok, timeset = message_authorised(message,host,control_port,missing_share_count)
    if not ok:
        print(f"failed to authorise message")
        return False, timeset
    #print(f"time to authorise message: {timeset["auth_time"]*1000} ms")

    message = json.loads(message)
    end_time=time.time()

    match message["function"]:
        case "write_register":
            response = write_register(host, modbus_port, address,value)
        case "read_register":
            response = read_register_address(host,modbus_port)

    #print(f"mtu send message response: {response}, time to send: {end_time*1000} ms",flush=True)

    timeset["send_message"] =time.time() - end_time
    return not response.isError(), timeset


def debug_send_message_no_authorisation(message, host, control_port, modbus_port, address, value, timeout=5.0, missing_share_count=0):
    timeset = {}
    end_time=time.time()

    client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
    client.connect()
    response = client.write_register(address, value, device_id=1)

    #print(f"mtu send message response: {response}, time to send: {end_time*1000} ms",flush=True)
    client.close()

    timeset["send_message"] =time.time() - end_time
    return not response.isError(), timeset

def write_register(host, modbus_port, address, value,timeout=5.0):
    client = ModbusTcpClient(host, port=modbus_port, timeout=timeout)
    client.connect()
    response = client.write_register(address, value, device_id=1)
    client.close()
    return response

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

    trial_res = {}

    res = []
    auth_time_res=[]
    value = [1,2]
    for i in range(0, trial_count):
        time_cost={}

        test_name = "legitimate_command"

        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        print(f"--- 1) {test_name}: target={target} addr={register_address} value={val} ---")
        end_time = time.time()

        msg, time_cost["make_message"]= make_message(target, "write_register", register_address, val)    
        

        ok, time_cost["send_message_set"] = send_message(msg, host, control_port, modbus_port, register_address, val)

        end_time = time.time() - end_time

        response_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {response_value[0]==val}, time: {end_time*1000} ms\n",flush=True)

        time_cost["total_time"] = end_time 

        print(f"time to make message: {time_cost["make_message"]*1000} ms")
        print(f"time to send_message: {time_cost["send_message_set"]["send_message"]*1000} ms")
        print(f"time to authorise message: {time_cost["send_message_set"]["total_auth_time"]*1000} ms")
        print(f" --- time to collect shares: {time_cost["send_message_set"]["share_collection"]*1000} ms")
        print(f" --- time to construct key: {time_cost["send_message_set"]["key_construction"]*1000} ms")
        print(f" --- time to sign message: {time_cost["send_message_set"]["message_signature_time"]*1000} ms")
        print(f" --- time to zeroise key: {time_cost["send_message_set"]["zeroise_time"]*1000} ms")
        print(f" --- time to connect authorisation: {time_cost["send_message_set"]["auth_time"]*1000} ms")
        print(f"total time: {time_cost["total_time"]*1000} ms\n")

        auth_time_res.append(time_cost)
        res.append({"correct_result": ok==True, "value_change_correct":response_value[0]==val ,"time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [3,4]
    for i in range(0, trial_count):
        test_name = "replay_message"
        print(f"--- 2) {test_name} without new authorisation (should be rejected) ---")
        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        msg,_ = make_message(target, "write_register", register_address, val)
        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, val)

        temp_val = initial_value
        initial_value = read_register_address(host, modbus_port,register_address)

        print(f"first authenticated message result authorised={ok}, init value: {temp_val}, final_value: {initial_value} ",flush=True)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        end_time = time.time()

        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, val)  

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)

        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)
        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [5,6]
    for i in range(0, trial_count):
        test_name = "wrong_target"
        print(f"--- 3) {test_name} (should be rejected) ---")
        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        end_time = time.time()

        msg,_ = make_message("not_a_real_plc", "write_register", register_address, val)  
        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, val)

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value,"time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [7,8]
    for i in range(0, trial_count):
        test_name = "mismatched_values"
        print(f"--- 4) {test_name} between signed message and actual write (should be rejected) ---")

        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        end_time = time.time()

        msg,_ = make_message(target, "write_register", register_address, val)
        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, 9999)  # different value than what was signed

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [9,10]
    for i in range(0, trial_count):
        test_name = "outdated_ts"
        print(f"--- 5) {test_name} (should be rejected) ---")

        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        end_time = time.time()

        msg,_ = make_message(target, "write_register", register_address, val,time.time() - 100)
        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, val)  

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [11,12]
    for i in range(0, trial_count):
        test_name = "missing_shares"
        print(f"--- 6) {test_name} (should be rejected) ---")

        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        end_time = time.time()

        msg,_ = make_message(target, "write_register", register_address, val,time.time())
        ok,_ = send_message(msg, host, control_port, modbus_port, register_address, val, missing_share_count=2)  

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    res=[]
    value = [13,14]
    for i in range(0, trial_count):
        test_name = "authorisation_skip"
        print(f"--- 7) {test_name} (should be rejected) ---")

        initial_value = read_register_address(host, modbus_port,register_address)

        val = value[False]
        if val == initial_value[0]:
            val = value[True]

        print(f"val={val}")

        end_time = time.time()

        msg,_ = make_message(target, "write_register", register_address, val,time.time())
        ok,_ = debug_send_message_no_authorisation(msg, host, control_port, modbus_port, register_address, val)      

        end_time = time.time() - end_time
        final_value = read_register_address(host, modbus_port,register_address)
        print(f"result: {ok}, value_change_correct: {initial_value==final_value}, time: {end_time*1000} ms\n",flush=True)

        res.append({"correct_result": ok==False, "value_change_correct":final_value==initial_value, "time": end_time})

    trial_res[test_name]=res

    evaluation.mtu_test_run(auth_time_res,trial_res,k,n)


if __name__ == "__main__":
    test_run(int(os.environ.get("TRIAL_COUNT")))

