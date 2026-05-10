import hashlib
import hmac
import time
import json
import requests
import os


class DeltaClient:

    BASE_URL = "https://api.delta.exchange"

    PRODUCT_IDS = {
        "BTCUSDT" : 84,
        "ETHUSDT" : 1699,
    }

    def __init__(self):
        self.api_key    = os.environ.get("DELTA_API_KEY")
        self.api_secret = os.environ.get("DELTA_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError("DELTA_API_KEY and DELTA_API_SECRET must be set")

    def _sign(self, method, path, body=""):
        timestamp = str(int(time.time()))
        msg       = method + timestamp + path + body
        signature = hmac.new(
            self.api_secret.encode(),
            msg.encode(),
            hashlib.sha256
        ).hexdigest()
        return {
            "api-key"      : self.api_key,
            "timestamp"    : timestamp,
            "signature"    : signature,
            "Content-Type" : "application/json"
        }

    def _get_product_id(self, symbol):
        product_id = self.PRODUCT_IDS.get(symbol.upper())
        if not product_id:
            raise ValueError(f"Unknown symbol: {symbol}")
        return product_id

    def place_order(self, symbol, side, qty, sl=0, tp=0):
        path = "/v2/orders"
        body = {
            "product_id"    : self._get_product_id(symbol),
            "size"          : qty,
            "side"          : side,
            "order_type"    : "market_order",
            "time_in_force" : "gtc"
        }
        body_str = json.dumps(body)
        headers  = self._sign("POST", path, body_str)

        resp = requests.post(
            self.BASE_URL + path,
            headers=headers,
            data=body_str,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def close_position(self, symbol):
        path     = "/v2/positions/close_all"
        body     = {"product_id": self._get_product_id(symbol)}
        body_str = json.dumps(body)
        headers  = self._sign("POST", path, body_str)

        resp = requests.post(
            self.BASE_URL + path,
            headers=headers,
            data=body_str,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    def get_position(self, symbol):
        path    = f"/v2/positions?product_id={self._get_product_id(symbol)}"
        headers = self._sign("GET", path)

        resp = requests.get(
            self.BASE_URL + path,
            headers=headers,
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()
