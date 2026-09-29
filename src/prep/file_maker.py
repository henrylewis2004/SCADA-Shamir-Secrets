import dealer
import nodes

import yaml

N_COUNT = 5
K_THRESHOLD = 3
SHAREHOLDER_PORT = 7000
REAL_SHARE_PATH = "./shares/share_files/"
REAL_NODE_LIST_PATH = "./shares/shareholders/"
REAL_NODE_LIST_FILENAME = "node_shareholder_list.json"

MTUS = 1
FIELD_DEVICES = 3

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

def make_docker_compose(mtu_count=MTUS, field_device_count=FIELD_DEVICES, n=N_COUNT, k=K_THRESHOLD, share_port=SHAREHOLDER_PORT):
    services = {}

    #mtu
    for i in range(1, mtu_count+1):
        name = f"mtu_{i}"
        services[name] = {
                "build":{
                    "context": ".",
                    "dockerfile": "src/mtu/Dockerfile"
                    },
                "environment":{
                    "K_THRESHOLD": k,
                    "N_COUNT": n,
                    "MTU_NAME": name,
                    "NODE_LIST_PATH":"/app/shares/shareholders/node_shareholder_list.json"
                    },
                "volumes": [f"{REAL_NODE_LIST_PATH}{REAL_NODE_LIST_FILENAME}:/app/shares/shareholders/node_shareholder_list.json:ro"],
                "networks": ["SCADA-system"],
                "depends_on": mtu_dependencies(field_device_count)
                }

    #field devices
    for i in range(1, field_device_count+1):
        name = f"field_device_{i}"
        services[name] = {
                "build":{
                    "context": ".",
                    "dockerfile": "src/field_device/Dockerfile"
                    },
                "environment":{
                    "K_THRESHOLD": k,
                    "N_COUNT": n,
                    "DEVICE_NAME": name,
                    "NODE_LIST_PATH":"/app/shares/shareholders/node_shareholder_list.json"
                    },
                "volumes": [f"{REAL_NODE_LIST_PATH}{REAL_NODE_LIST_FILENAME}:/app/shares/shareholders/node_shareholder_list.json:ro"],
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
    dealer.deal(N_COUNT,K_THRESHOLD)
    nodes.make_node_file(N_COUNT,REAL_NODE_LIST_PATH, REAL_SHARE_PATH, port=SHAREHOLDER_PORT)
    make_docker_compose()

