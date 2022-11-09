import json
import os

import requests


def send_request(ip="127.0.0.1", port=9860):
    url = f"http://{ip}:{port}"
    data = "0123456789"
    req = {"function": "test"}

    headers = {"json-request": json.dumps(req)}
    response = requests.post(url, data, headers=headers)
    print(response.text)

if __name__ == "__main__":
    send_request()