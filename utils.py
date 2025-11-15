# utils.py
import os
import re
import json
from datetime import datetime

def validate_email(email):
    # basic regex
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(regex, email.strip()))

def validate_phone(phone):
    # accept digits, spaces, +, -, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    cleaned = cleaned.lstrip('+')
    return cleaned.isdigit() and (7 <= len(cleaned) <= 15)

def save_to_json(obj, path="data/submissions.json"):
    # ensure folder exists
    folder = os.path.dirname(path)
    if folder and not os.path.exists(folder):
        os.makedirs(folder, exist_ok=True)
    # if file exists, append
    data = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except:
            data = []
    data.append(obj)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print("Error saving:", e)
        return False

def load_env_defaults():
    # set defaults if not present
    if "STORAGE_FILE" not in os.environ:
        os.environ["STORAGE_FILE"] = "data/submissions.json"
    # ensure model variable exists
    if "OPENAI_MODEL" not in os.environ:
        os.environ["OPENAI_MODEL"] = "gpt-4"
