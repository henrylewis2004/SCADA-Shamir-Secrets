import json
import os

from dealer import  node_list_dir, shares_dir
 

def build_nodes(n, shareholder_dir=shares_default_dir, port=7000):
    nodes = []

    for x in range(1, n + 1):
        path = os.path.join(shareholder_dir, f"shareholder_{x}.json")

        with open(path) as file:
            data = json.load(file)

        assert data["x"] == x, f"mismatch: file shareholder_{x}.json claims x={data['x']}"
        nodes.append({"url": f"http://shareholder{x}:{port}/share","token": data["api_token"],})

    return nodes

def make_node_file(n, output_dir=node_list_default_dir, shareholder_dir=shares_default_dir, port=7000):
    nodes = build_nodes(shareholder_dir,n,port)

    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,"node_shareholder_list.json")

    with open(filename, "w") as file:
        json.dump(nodes, file, indent=2)


    print(f"node_shareholder_list.json populated at {filename}")


def load_nodes(node_list_dir=node_list_default_dir,node_list_filename="node_shareholder_list.json"):
    path = os.path.join(node_list_dir,node_list_filename)

    with open(path) as file:
        return json.load(file)


    return nodes
