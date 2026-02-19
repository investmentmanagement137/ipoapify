import csv
import os
import time
from config_and_utils import COMPLETED_FILE, log

def is_already_completed(username, company_name):
    if not os.path.exists(COMPLETED_FILE): 
        return False
    try:
        with open(COMPLETED_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            return any(row['Username'] == username and row['Company'] == company_name for row in reader)
    except: 
        return False

async def save_completion(account_name, username, boid, company_name, url):
    file_exists = os.path.exists(COMPLETED_FILE)
    fieldnames = ['Name', 'Username', 'BOID', 'Company', 'URL', 'Applied At']
    
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    record = {
        'Name': account_name,
        'Username': username,
        'BOID': boid,
        'Company': company_name,
        'URL': url,
        'Applied At': timestamp
    }

    # 1. Apify Output
    if os.environ.get("APIFY_RUNNING") == "true":
        try:
            from apify import Actor
            await Actor.push_data(record)
            log(f"SUCCESS: {account_name} record pushed to Apify Dataset.")
        except Exception as e:
            log(f"Error pushing to Apify: {e}")

    # 2. Local CSV Output (Skip checks if on Apify since ephemeral)
    try:
        # Check if already exists to prevent duplicate rows in CSV (Local only)
        if os.environ.get("APIFY_RUNNING") != "true" and is_already_completed(username, company_name):
            return

        with open(COMPLETED_FILE, mode='a', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(record)
        
        if os.environ.get("APIFY_RUNNING") != "true":
             log(f"SUCCESS: {account_name} record saved for {company_name}.")
    except Exception as e:
        # On Apify, CSV errors are expected if not found, suppress them or log debug
        if os.environ.get("APIFY_RUNNING") != "true":
            log(f"Error saving history to CSV: {e}")

def get_applied_list():
    if not os.path.exists(COMPLETED_FILE):
        return []
    data = []
    try:
        with open(COMPLETED_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except:
        pass
    return data

def migrate_json_history():
    """Check for completed_applications.json and migrate to CSV."""
    import json
    import shutil
    
    # Check current and parent directory
    json_candidates = ["completed_applications.json", "../completed_applications.json"]
    
    for json_path in json_candidates:
        if os.path.exists(json_path):
            try:
                log(f"Found legacy history: {json_path}. Migrating...")
                with open(json_path, 'r', encoding='utf-8') as f:
                    old_data = json.load(f)
                
                if not isinstance(old_data, list):
                    log(f"Skipping {json_path}: Not a list.")
                    continue

                count = 0
                for item in old_data:
                    company = item.get('company')
                    username = item.get('username')
                    
                    if company and username:
                        if not is_already_completed(username, company):
                            # Append to CSV
                             save_completion(
                                item.get('user_name', ''),
                                username,
                                item.get('boid', ''),
                                company,
                                item.get('url', '')
                            )
                             count += 1
                
                log(f"Migrated {count} records from {json_path}.")
                
                # Backup/Rename to avoid re-migration
                shutil.move(json_path, json_path + ".bak")
                log(f"Renamed {json_path} to {json_path}.bak")
                
            except Exception as e:
                log(f"Error migrating {json_path}: {e}")

if __name__ == "__main__":
    # Auto-migrate on run
    migrate_json_history()

    history = get_applied_list()
    if not history:
        print("No application history found.")
    else:
        print(f"{'Username':<15} | {'Company':<30} | {'Date':<20}")
        print("-" * 70)
        for entry in history:
            print(f"{entry.get('Username', 'N/A'):<15} | {entry.get('Company', 'N/A'):<30} | {entry.get('Applied At', 'N/A'):<20}")
