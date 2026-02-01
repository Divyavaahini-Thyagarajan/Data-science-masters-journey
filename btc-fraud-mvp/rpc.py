import requests
from requests.auth import HTTPBasicAuth

class BitcoinRPC:
    def __init__(self, url: str, user: str, password: str, timeout: int = 60):
        self.url = url
        self.auth = HTTPBasicAuth(user, password)
        self.timeout = timeout
        self._id = 0

    def call(self, method: str, params=None):
        if params is None:
            params = []
        self._id += 1
        payload = {"jsonrpc": "1.0", "id": self._id, "method": method, "params": params}
        r = requests.post(self.url, json=payload, auth=self.auth, timeout=self.timeout)
        r.raise_for_status()
        data = r.json()
        if data.get("error"):
            raise RuntimeError(f"RPC error: {data['error']}")
        return data["result"]
