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

def make_node_file(n, output_dir, shareholder_dir, port=7000):
    nodes = build_nodes(n,shareholder_dir,port)

    os.makedirs(output_dir,exist_ok=True)
    filename = os.path.join(output_dir,"node_shareholder_list.json")

    with open(filename, "w") as file:
        json.dump(nodes, file, indent=2)


    print(f"node_shareholder_list.json populated at {filename}")


def load_nodes(path):
    with open(path) as file:
        return json.load(file)

    return nodes
