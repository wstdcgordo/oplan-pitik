import mariadb, json
from dotenv import load_dotenv
from getmac import get_mac_address
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
data_creds = os.path.join(current_dir, '..', '[credential_folder]', '[env_name].env')
load_dotenv(data_creds)

class goyaz:
    def __init__(self, db_name="pitik_main", host=None, user=None, password=None, port=None):
        try:
            port = int(os.getenv('PORT', 3306))
        except Exception as e:
            print(f"❌ [CONFIG ERROR] {e}")
            port = 3306
            
        self.config = {
            'user': os.getenv('DB_USER'),
            'password': os.getenv('DB_PASSWORD'),
            'host': os.getenv('HOST'),
            'port': port,
            'database': os.getenv('DATABASE')
        }
        
    def footprint(self):
        mac = get_mac_address()
        return mac

    def commit_record(self, clean_data, row_hash, prev_hash):
        if not self.config['database']:
            print("❌ [CONFIG ERROR] Database name is missing in environment variables.")
            return False
        
        try:
            conn = mariadb.connect(**self.config)
            cur = conn.cursor()

            sql_main = """
                INSERT INTO table_name (
                    business_id_no, business_name, ..., raw_ocr_json, 
                    prev_hash, row_hash
                ) VALUES (?, ?, ..., ?, ?, ?)
            """ # The quantities and order of columns should match the values_main below
            
            values_main = (
                clean_data.get('business_id_no'),
                clean_data.get('business_name'),
                # ... (all other fields in the same order as the SQL above)
                clean_data.get('total_grand_calc'),
                json.dumps(clean_data),
                prev_hash,
                row_hash
            )

            cur.execute(sql_main, values_main)

            sql_audit = """
                INSERT INTO hidden_audit_log (
                    target_row_hash, 
                    processor_mac, 
                    business_id_no, 
                    event_type
                ) VALUES (?, ?, ?, ?)
            """
            cur.execute(sql_audit, (
                row_hash, 
                self.footprint(),
                clean_data.get('business_id_no'), 
                "VALIDATED_INGEST"
            ))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"❌ [CRITICAL DB ERROR] {e}")
            return False