import json
import os

def build_roster(shareholder_dir, n, port=7000):
    roster = []

    for x in range(1, n + 1):
        path = os.path.join(shareholder_dir, f"shareholder_{x}.json")

        with open(path) as file:
            data = json.load(f)

        assert data["x"] == x, f"mismatch: file shareholder_{x}.json claims x={data['x']}"
        roster.append({"url": f"http://shareholder{x}:{port}/share","token": data["api_token"],})

    return roster
