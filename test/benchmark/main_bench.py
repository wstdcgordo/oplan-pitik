import os
from statistics import mode
import time
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from core.processors import rodri_bench
from core.security import gusman_bench
from core.database import goyaz_bench, goyaz_bigquery_bench, goyaz_aws_bench
from pathlib import Path

# 1. Kunin ang absolute path kung nasaan itong main_bench.py
script_dir = Path(__file__).resolve().parent

# 2. I-point sa test.env na nasa parent directory (yung ../ version)
env_path = script_dir.parent / 'test.env'

# 3. I-load gamit ang absolute path
load_dotenv(dotenv_path=env_path)

COORDS_PATH = os.getenv("COORDS_JSON_PATH")
IMAGE_PATH = os.getenv("IMAGE_INPUT_PATH")
KEY_PATH = os.getenv('BQ_CRED_KEY_PATH')

tiers = {
    "1": {"name": "Small (30k pop)", "volume": 900, "db": "pitik_small"},
    "2": {"name": "Medium (100k pop)", "volume": 3000, "db": "pitik_medium"},
    "3": {"name": "Large (300k pop)", "volume": 9000, "db": "pitik_large"},
    "4": {"name": "Huge (500k pop)", "volume": 15000, "db": "pitik_huge"},
    "5": {"name": "Mega (1M pop)", "volume": 30000, "db": "pitik_mega"},
    "6": {"name": "Metropolis (QC Scale)", "volume": 78000, "db": "pitik_qc"}
}

def run_bench(mode, choice):
    tier_info = tiers[choice]
    sample_size = 100 if choice == "1" else (150 if choice == "2" else 300)
    
    # Init modules
    processor = rodri_bench(COORDS_PATH)
    hasher = gusman_bench()
    
    vault = None
    if mode == 'local':
        vault = goyaz_bench(db_name=tier_info['db'])
    elif mode == 'cloud_bq':
        vault = goyaz_bigquery_bench(dataset_id=tier_info['db'], key_path=KEY_PATH)
    elif mode == 'cloud_aws':
        vault = goyaz_aws_bench(db_name=tier_info['db']) # AWS RDS mode!
    
    if vault is None:
        raise ValueError(f"Invalid mode: {mode}")
        
    vault.open_session()
    
    results = []

    print(f"\n🚀 STARTING {mode.upper()} BENCHMARK: {tier_info['name']}")
    
    try:
        for i in range(sample_size):
            start = time.perf_counter()
            _dummy = np.random.randint(0, 255, (5475, 4050), dtype=np.uint8) # Stress memory
            
            data = processor.extract_data(IMAGE_PATH)
            r_hash = hasher.generate_pitik_hash(data)
            success = vault.commit_record(data, r_hash, f"PREV_{i}")
            
            end = time.perf_counter()
            results.append({"tier": tier_info['name'], "iteration": i, "latency_sec": end - start, "status": "SUCCESS" if success else "FAILED"})
            print(f"   ⚡ [{i+1}/{sample_size}] Latency: {end-start:.4f}s", end="\r")
            del _dummy
            
    finally:
        vault.close_session()

    return pd.DataFrame(results)

if __name__ == "__main__":
    mode = input("Select Mode (local / cloud_bq / cloud_aws): ").lower()
    choice = input("Select Tier (1-6): ")
    if choice in tiers:
        # AUTOMATIC FOLDER CREATION PARA HINDI NA MAG-ERROR
        save_path = os.getenv("BENCHMARK_SAVE_PATH")
        if save_path:
            os.makedirs(save_path, exist_ok=True)
        
        df = run_bench(mode, choice)
        print(f"\n✅ Done. Average Latency: {df['latency_sec'].mean():.4f}s")
        
        df.to_csv(f"{save_path}benchmark_{mode}_{choice}.csv", index=False)