import json
import os

#from dealer import out_dir, shares_dir
#node_list_dir = os.path.join(out_dir,"shareholders")

def build_nodes(n, shareholder_dir, port):
    nodes = []

    for x in range(1, n + 1):
        path = os.path.join(shareholder_dir, f"shareholder_{x}.json")

        with open(path) as file:
            data = json.load(file)

        assert data["x"] == x, f"mismatch: file shareholder_{x}.json claims x={data['x']}"
        nodes.append({"url": f"http://shareholder_{x}:{port}/share","token": data["shareholder_token"],})

    return nodes

def make_node_file(n, output_dir, output_filename, shareholder_dir, port=7000):
    nodes = build_nodes(n,shareholder_dir,port)

    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,output_filename)

    print(filename)

    with open(filename, "w") as file:
        json.dump(nodes, file, indent=2)


    print(f"shareholder list populated at {filename}")


def make_field_device_file(count, output_dir, output_filename, control_port, modbus_port, name_format="field_device_"):
    devices = {}
    
    for i in range(1,count+1):
        devices[name_format+str(i)] = {"host":name_format+str(i), "control_port": control_port, "modbus_port": modbus_port}

    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,output_filename)

    with open(filename, "w") as file:
        json.dump(devices, file, indent=2)


    print(f"field devices list populated at {filename}")



def load_nodes(path):
    with open(path) as file:
        return json.load(file)

    return nodes

