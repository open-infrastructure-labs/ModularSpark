import json
import requests


class ServerTest:

    ip_default = "127.0.0.1"
    port_default = 9860

    def get_percentage(self, ip=None, port=None):
        if ip is None:
            ip = ServerTest.ip_default
        if port is None:
            port = ServerTest.port_default
        url = f"http://{ip}:{port}"
        data = "0123456789"
        req = {"table": "store_sales", "query": "SELECT * FROM store_sales WHERE ss_quantity > '1'"}
        headers = {"request-json": json.dumps(req)}
        response = requests.post(url, data, headers=headers)
        print(response.text)

    def get_tables(self, ip=None, port=None):
        if ip is None:
            ip = ServerTest.ip_default
        if port is None:
            port = ServerTest.port_default
        url = f"http://{ip}:{port}"
        payload = {'op': 'GET_TABLES'}
        response = requests.post(url, params=payload)
        print(response.text)


if __name__ == "__main__":
    st = ServerTest()
    st.get_tables()
    st.get_percentage()
