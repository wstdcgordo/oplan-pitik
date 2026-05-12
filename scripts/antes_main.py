from buscape import rodri
from rocinha import goyaz
from surquillo import gusman
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(current_dir, '..', 'src'))

def run_test():
    # Setup
    processor = rodri(os.getenv("COORDS_JSON_PATH"))
    vault = goyaz()
    hasher = gusman()
    
    # 1. OCR & Cleaning
    print("🚀 Extracting & Cleaning Data...")
    clean_data = processor.extract_data(os.getenv("IMAGE_INPUT_PATH"))

    # 2. Security Hashing
    print("🔒 Generating Security Hash...")
    new_hash = hasher.generate_pitik_hash(data=clean_data)
    
    # 3. Ingestion
    print("📥 Committing to MariaDB...")
    if vault.commit_record(clean_data, new_hash, "GENESIS_BLOCK"):
        print("✅ SUCCESS: Record secured in Vault.")
    else:
        print("❌ FAILED: Ingestion error.")

if __name__ == "__main__":
    run_test()