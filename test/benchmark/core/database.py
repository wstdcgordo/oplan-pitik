import os
import json
import re
import mariadb
import yaml
from datetime import datetime
from getmac import get_mac_address
from google.cloud import bigquery
from google.oauth2 import service_account
from .datavault import DatabaseServiceManager
from dotenv import load_dotenv

load_dotenv('test/test.env')

# ----------------------------------------------------------------------
# Load YAML once
# ----------------------------------------------------------------------
def load_config(yaml_path=os.getenv('SQL_QUERIES_PATH', 'sql_queries.yaml')):
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

CONFIG = load_config()

# ----------------------------------------------------------------------
# Helper to build payload from data and valid_columns
# ----------------------------------------------------------------------
def build_payload(data, valid_columns, row_hash, prev_hash):
    payload = {k: v for k, v in data.items() if k in valid_columns}
    total_val = data.get('total_grand_calc', 0)
    if isinstance(total_val, str):
        total_val = re.sub(r'[^0-9.]', '', total_val.replace(',', ''))
    payload['total_grand'] = float(total_val) if total_val else 0.0
    payload['raw_ocr_json'] = json.dumps(data)
    payload['row_hash'] = row_hash
    payload['prev_hash'] = prev_hash
    return payload

# ----------------------------------------------------------------------
# Local MariaDB
# ----------------------------------------------------------------------
class goyaz_bench:
    def __init__(self, db_name):
        self.db_name = db_name
        self.config = {
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': self.db_name
        }
        self.conn = None
        self.queries = CONFIG['mariadb']
        self.valid_columns = self.queries['valid_columns']
        self._prepare_environment()
        self.open_session()

    def open_session(self):
        if not self.conn:
            # Use the separated service manager
            if DatabaseServiceManager.ensure_running():
                if not DatabaseServiceManager.wait_until_ready(
                    host=self.config['host'],
                    port=self.config['port'],
                    user=self.config['user'],
                    password=self.config['password']
                ):
                    raise ConnectionError("Database not ready after starting service.")
            self.conn = mariadb.connect(**self.config)
            print(f"🔗 Session Opened: {self.db_name}")

    def close_session(self):
        if self.conn:
            self.conn.close()
            self.conn = None
            print("🔒 Session Closed.")
            
    def _prepare_environment(self):
        try:
            # Create database
            conn = mariadb.connect(
                user=self.config['user'],
                password=self.config['password'],
                host=self.config['host'],
                port=self.config['port']
            )
            cur = conn.cursor()
            query_string = str(self.queries['create_database']).replace("{db_name}", str(self.db_name))
            cur.execute(query_string)
            conn.close()

            conn = mariadb.connect(**self.config)
            cur = conn.cursor()
            cur.execute(self.queries['create_main_table'])
            cur.execute(self.queries['create_audit_log'])
            conn.close()
            print(f"✅ Environment ready: {self.db_name}")
        except Exception as e:
            print(f"⚠️ [SETUP] {e}")

    def commit_record(self, data, row_hash, prev_hash):
        try:
            if not self.conn:
                self.open_session()
            cur = self.conn.cursor()
            payload = build_payload(data, self.valid_columns, row_hash, prev_hash)
            columns = ", ".join(payload.keys())
            placeholders = ", ".join(["?"] * len(payload))
            sql_main = self.queries['insert_table_name_template'].format(
                columns=columns, placeholders=placeholders
            )
            safe_sql = f"{sql_main}"
            cur.execute(safe_sql, list(payload.values())) # nosec
            cur.execute(self.queries['insert_audit_log'], (
                row_hash,
                get_mac_address(),
                data.get('business_id_no', 'N/A'),
                self.queries['event_type_local']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ [DB ERROR] {e}")
            return False

# ----------------------------------------------------------------------
# AWS RDS (inherits from goyaz_bench, overrides event type)
# ----------------------------------------------------------------------
class goyaz_aws_bench(goyaz_bench):
    def __init__(self, db_name):
        # Override config with AWS environment variables
        self.db_name = db_name
        self.config = {
            'user': os.getenv('AWS_RDS_USER'),
            'password': os.getenv('AWS_RDS_PASSWORD'),
            'host': os.getenv('AWS_RDS_ENDPOINT'),
            'port': int(os.getenv('AWS_RDS_PORT', 3306)),
            'database': self.db_name,
            'ssl': {'ca': None, 'verify_server_cert': False}
        }
        self.conn = None
        self.queries = CONFIG['mariadb']
        self.valid_columns = self.queries['valid_columns']
        self._prepare_environment()

    def commit_record(self, data, row_hash, prev_hash):
        try:
            if not self.conn:
                self.open_session()
            cur = self.conn.cursor()
            payload = build_payload(data, self.valid_columns, row_hash, prev_hash)
            columns = ", ".join(payload.keys())
            placeholders = ", ".join(["?"] * len(payload))
            sql_main = self.queries['insert_table_name_template'].format(
                columns=columns, placeholders=placeholders
            )
            cur.execute(sql_main, list(payload.values()))
            cur.execute(self.queries['insert_audit_log'], (
                row_hash,
                get_mac_address(),
                # data.get('business_id_no', 'N/A'), # # Suited for BPLS only, put 'N/A' or some default if not available
                self.queries['event_type_aws']
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"❌ [AWS RDS ERROR] {e}")
            return False

# ----------------------------------------------------------------------
# BigQuery
# ----------------------------------------------------------------------
class goyaz_bigquery_bench:
    def __init__(self, dataset_id, key_path):
        self.dataset_id = dataset_id
        self.creds = service_account.Credentials.from_service_account_file(key_path)
        self.client = bigquery.Client(credentials=self.creds, project=self.creds.project_id)
        self.project = self.client.project
        self.table_name = "put_your_table_name_here"  # Placeholder, will be set in _prepare_environment
        self.main_table = f"{self.project}.{self.dataset_id}.{self.table_name}"
        self.audit_table = f"{self.project}.{self.dataset_id}.hidden_audit_log"
        self.queries = CONFIG['bigquery']
        self.valid_columns = self.queries['valid_columns']
        self._prepare_environment()

    def open_session(self):
        print(f"☁️ BigQuery Ready: {self.dataset_id}")

    def close_session(self):
        print("☁️ BigQuery Finished.")

    def _prepare_environment(self):
        try:
            dataset = bigquery.Dataset(f"{self.project}.{self.dataset_id}")
            dataset.location = "asia-southeast1"
            self.client.create_dataset(dataset, exists_ok=True)
            create_main_sql = self.queries['create_main_table_template'].format(
                project=self.project, dataset_id=self.dataset_id
            )
            create_audit_sql = self.queries['create_audit_log_template'].format(
                project=self.project, dataset_id=self.dataset_id
            )
            self.client.query(create_main_sql).result()
            self.client.query(create_audit_sql).result()
            print(f"✅ BigQuery ready: {self.dataset_id}")
        except Exception as e:
            print(f"⚠️ [BQ SETUP] {e}")

    def commit_record(self, data, row_hash, prev_hash):
        try:
            payload = build_payload(data, self.valid_columns, row_hash, prev_hash)
            payload['timestamp'] = datetime.utcnow().isoformat()
            errors = self.client.insert_rows_json(self.main_table, [payload])
            if errors:
                raise Exception(f"Main table error: {errors}")
            audit_payload = {
                "target_row_hash": row_hash,
                "processor_mac": get_mac_address(),
                # "business_id_no": data.get('business_id_no', 'N/A'), # # Suited for BPLS only, put 'N/A' or some default if not available
                "event_type": self.queries['event_type'],
                "timestamp": datetime.utcnow().isoformat()
            }
            errors_audit = self.client.insert_rows_json(self.audit_table, [audit_payload])
            if errors_audit:
                raise Exception(f"Audit table error: {errors_audit}")
            return True
        except Exception as e:
            print(f"❌ [BQ ERROR] {e}")
            return False