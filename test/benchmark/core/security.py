import json
import hashlib
import hmac

class gusman_bench:
    def generate_pitik_hash(self, data, prev_hash="GENESIS_BLOCK"):
        data_str = json.dumps(data, sort_keys=True)
        h = hmac.new(prev_hash.encode(), data_str.encode(), digestmod=hashlib.sha3_256)
        return h.hexdigest()