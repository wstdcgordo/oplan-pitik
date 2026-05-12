from getmac import get_mac_address
import hashlib, hmac
import json

class gusman:
    def footprint(self):
        mac = get_mac_address()
        return mac

    def generate_pitik_hash(self, data, prev_hash="GENESIS_BLOCK"):
        # Security Layer
        data_str = json.dumps(data, sort_keys=True)
        h = hmac.new(prev_hash.encode(), data_str.encode(), digestmod=hashlib.sha3_256)
        
        return h.hexdigest()