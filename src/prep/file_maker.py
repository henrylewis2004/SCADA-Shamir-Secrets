import dealer
import nodes

import yaml

N_COUNT = 5
K_THRESHOLD = 3
SHAREHOLDER_PORT = 7000

REAL_SHARE_PATH = "./config/share_files/"
REAL_NODE_LIST_PATH = "./config/shareholders/"
REAL_NODE_LIST_FILENAME = "node_shareholder_list.json"
NODE_LIST_PATH = "/app/config/node_shareholder_list.json"

REAL_FIELD_DEVICE_LIST_PATH = "./config/field_devices/"
REAL_FIELD_DEVICE_LIST_FILENAME = "field_device_list.json"
FIELD_DEVICE_LIST_PATH = "/app/config/field_devices.json"

CONTAINER_EVAL_DIR = "/app/eval/"
REAL_EVAL_DIR = "./eval/"
    
FIELD_DEVICES_CONTROL_PORT = 6000
FIELD_DEVICES_MODBUS_PORT = 5020

MTU_COUNT = 1
FIELD_DEVICE_COUNT = 3

def mtu_dependencies(count):
    dep = []
    for i in range(1, count + 1):
        dep.append(f"field_device_{i}")

    return dep

def field_device_dependencies(count):
    dep = []
    for i in range(1, count + 1):
        dep.append(f"shareholder_{i}")

    return dep

def make_docker_compose(mtu_count=MTU_COUNT, field_device_count=FIELD_DEVICE_COUNT, n=N_COUNT, k=K_THRESHOLD, share_port=SHAREHOLDER_PORT):
    services = {}

    #mtu
    real_node_list_path = REAL_NODE_LIST_PATH + REAL_NODE_LIST_FILENAME
    real_device_list_path = REAL_FIELD_DEVICE_LIST_PATH + REAL_FIELD_DEVICE_LIST_FILENAME

    for i in range(1, mtu_count+1):
        name = f"mtu_{i}"
        services[name] = {
                "build":{
                    "context": ".",
                    "dockerfile": "src/mtu/Dockerfile"
                    },
                "environment":{
                    "K_THRESHOLD": str(k),
                    "N_COUNT": str(n),
                    "MTU_NAME": name,
                    "NODE_LIST_PATH": NODE_LIST_PATH,
                    "FIELD_DEVICE_LIST_PATH": FIELD_DEVICE_LIST_PATH,
                    "FIELD_DEVICE_COUNT": FIELD_DEVICE_COUNT,
                    ##test variables
                    "TEST_TARGET": "field_device_1",
                    "TRIAL_COUNT": "5"
                    },
                "volumes": [f"{real_node_list_path}:{NODE_LIST_PATH}:ro",f"{real_device_list_path}:{FIELD_DEVICE_LIST_PATH}:ro",f"{REAL_EVAL_DIR}:{CONTAINER_EVAL_DIR}"],
                "networks": ["SCADA-system"],
                "depends_on": mtu_dependencies(field_device_count)
                }

    #field devices
    real_node_list_path = REAL_NODE_LIST_PATH + REAL_NODE_LIST_FILENAME

    for i in range(1, field_device_count+1):
        name = f"field_device_{i}"
        services[name] = {
                "build":{
                    "context": ".",
                    "dockerfile": "src/field_device/Dockerfile"
                    },
                "environment":{
                    "K_THRESHOLD": str(k),
                    "N_COUNT": str(n),
                    "DEVICE_NAME": name,
                    "NODE_LIST_PATH":NODE_LIST_PATH,
                    "IP_ADDRESS": "0.0.0.0",
                    "CONTROL_PORT":str(FIELD_DEVICES_CONTROL_PORT),
                    "MODBUS_PORT":str(FIELD_DEVICES_MODBUS_PORT)
                    },
                "volumes": [f"{real_node_list_path}:{NODE_LIST_PATH}:ro"],
                "networks": ["SCADA-system"],
                "depends_on": field_device_dependencies(n)
                }

    #shareholders
    for i in range(1,n + 1):
        name = f"shareholder_{i}"
        services[name] = {
                "build":{
                    "context": ".",
                    "dockerfile": "src/shareholder/Dockerfile"
                    },
                "environment":{
                    "PORT": str(share_port),
                    "NODE_NAME": name,
                    "SHARE_PATH": "/app/shares/share_files/share.json",
                    "EXPORT_SHARE_PATH": "/share"
                    },
                "volumes": [f"{REAL_SHARE_PATH}{name}.json:/app/shares/share_files/share.json:ro"],
                "networks": ["SCADA-system"]
                }

    networks = {
            "SCADA-system":{
                "driver": "bridge"
                }
            }

    compose = {"services": services, "networks": networks}

    with open("docker-compose.yml", "w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)

    print(f"docker-compose written")

if __name__ == "__main__":
    dealer.deal(N_COUNT,K_THRESHOLD,REAL_SHARE_PATH)
    nodes.make_node_file(N_COUNT,REAL_NODE_LIST_PATH, REAL_NODE_LIST_FILENAME, REAL_SHARE_PATH, port=SHAREHOLDER_PORT)
    nodes.make_field_device_file(FIELD_DEVICE_COUNT,REAL_FIELD_DEVICE_LIST_PATH, REAL_FIELD_DEVICE_LIST_FILENAME, FIELD_DEVICES_CONTROL_PORT, FIELD_DEVICES_MODBUS_PORT)
    make_docker_compose()

