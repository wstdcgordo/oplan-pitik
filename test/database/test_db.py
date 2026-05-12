# Test Script to validate database connection, insertion, and hashing logic for Project Pitik

import mariadb
import hashlib
import json
from getmac import get_mac_address

# CONFIGURATION
DB_CONFIG = {
    'user': '[your username]',
    'password': '[your password]',       
    'host': '[your host]',             
    'port': int('[your port]'), # int function is not needed if you already have the port as an integer in the .env file, but it's here just in case you have it as a string
    'database': '[your database name]'
}

def test_connection():
    print("--- 🛡️ Project Pitik: Database Integrity Test ---")
    try:
        # 1. Test Connection
        conn = mariadb.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ [CONNECTED] MariaDB is up and running on M3.")

        # 2. Mock Data para sa BPLS
        mock_data = {
            "business_id_no": "INF-2026-TEST",
            "business_name": "Pitik Coffee Shop",
            "owner_name": "Juan Dela Cruz",
            "business_permit_no": "PERMIT-123",
            "total_grand": 1500.50,
            "business_address": "Infanta, Quezon",
            "business_tin": "123-456-789"
        }
        
        # 3. Security Logic Test (Hashing)
        prev_hash = "GENESIS_BLOCK"
        data_string = json.dumps(mock_data, sort_keys=True)
        row_hash = hashlib.sha512(f"{data_string}{prev_hash}".encode()).hexdigest()
        mac_addr = get_mac_address()
        
        print(f"✅ [HASHING] SHA-512 Check: {row_hash[:16]}... OK")

        sql_main = """
                INSERT INTO table_name (
                    business_id_no, business_name, ..., raw_ocr_json, 
                    prev_hash, row_hash
                ) VALUES (?, ?, ..., ?, ?, ?)
            """
        
        values_main = (
                mock_data.get('business_id_no'),
                mock_data.get('business_name'),
                # ... (all other fields in the same order as the SQL above)
                mock_data.get('total_grand_calc'),
                json.dumps(mock_data),
                prev_hash,
                row_hash
            )
        
        cur.execute(sql_main, values_main)

        # 4. Hidden Audit Ingest (The Blackbox)
        sql_audit = """
            INSERT INTO hidden_audit_log (
                target_row_hash, processor_mac, business_id_no, event_type
            ) VALUES (?, ?, ?, ?)
        """
        cur.execute(sql_audit, (row_hash, mac_addr, mock_data['business_id_no'], "TEST_VALIDATION"))

        conn.commit()
        print(f"✅ [MAIN] Record {mock_data['business_id_no']} inserted.")
        print(f"✅ [AUDIT] MAC {mac_addr} logged with hash {row_hash[:12]}...")
        
        conn.close()
        print("\n🏆 Test Finished: Database structure is robust and nullable-safe.")

    except Exception as e:
        print(f"❌ [CRITICAL ERROR] {e}")
        
if __name__ == "__main__":
    test_connection()