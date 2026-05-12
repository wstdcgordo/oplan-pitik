import os
import sys
from dotenv import load_dotenv

# 1. Path Management
# Kunin ang absolute path ng directory kung nasaan itong loader.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Siguraduhin na ang 'src' ay nasa Python Path
if BASE_DIR not in sys.path:
    sys.path.append(os.path.join(BASE_DIR, 'src'))

# 2. Load Environment Variables
# Ang location ng .env ay relative sa BASE_DIR
env_path = os.path.join(BASE_DIR, '[credential_folder]', '[env_name].env')
load_dotenv(env_path)

def get_config():
    """
    Kinukuha ang lahat ng kailangan mula sa .env. 
    Walang hardcoded sensitive data dito.
    """
    return {
        "db_user": os.getenv('DB_USER'),
        "db_pass": os.getenv('DB_PASSWORD'),
        "db_name": os.getenv('DATABASE'),
        "db_host": os.getenv('HOST'),
        "db_port": int(os.getenv('PORT', 3306)),
        "coords": os.getenv('COORDS_JSON'),
        "input": os.getenv('IMAGE_INPUT_PATH') # or IMAGE_INPUT_PATH_S for directory for multiple images (max of 50)
    }