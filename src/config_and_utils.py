import csv
import time
import os

ACCOUNTS_FILE = "accounts.csv"
COMPLETED_FILE = "history.csv"

def load_accounts():
    accounts = []
    
    # 1. Apify Support (Injected by main.py or other means)
    # ACCOUNTS variable is global, so main.py can override it directly.
    # However, if we want to load here:
    # We rely on main.py injecting it into this module's ACCOUNTS variable *after* import.
    # But since this runs on import, we return empty or CSV data first.
    
    if not os.path.exists(ACCOUNTS_FILE):
        # Only log warning if not running in Apify, as Apify might use input only
        if os.environ.get("APIFY_RUNNING") != "true":
            log(f"Warning: {ACCOUNTS_FILE} not found.")
        return []
    
    try:
        # Use utf-8-sig for Excel compatibility with Nepali fonts
        with open(ACCOUNTS_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic validation: requires username
                if row.get("Username"):
                    accounts.append({
                        "name": row.get("Name", row.get("Username")),
                        "active": str(row.get("Active", "True")).lower() == "true",
                        "dp_id": row.get("DP ID", ""),
                        "username": row.get("Username", ""),
                        "password": row.get("Password", ""),
                        "crn": row.get("CRN", ""),
                        "pin": row.get("PIN", ""),
                        "bank_name": row.get("Bank Name", ""),
                        "status": row.get("Status", ""),
                        "available_banks": row.get("Available Banks", "")
                    })
    except Exception as e:
        log(f"Error loading {ACCOUNTS_FILE}: {e}")
    return accounts

ACCOUNTS = load_accounts()

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted_msg = f"[{timestamp}] {message}"
    print(formatted_msg)
    try:
        with open("automation.log", "a", encoding='utf-8') as f:
            f.write(formatted_msg + "\n")
    except:
        pass

def update_account_status(username, key, value):
    """Update status in CSV. For simplicity, we write to the 'Status' column or just log."""
    try:
        temp_accounts = []
        updated = False
        with open(ACCOUNTS_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            for row in reader:
                if row["Username"] == username:
                    row["Status"] = "OK" if value else f"Failed {key}"
                    updated = True
                temp_accounts.append(row)
        
        if updated:
            with open(ACCOUNTS_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(temp_accounts)
    except Exception as e:
        log(f"Error updating CSV: {e}")

def save_account_banks(username, banks_list):
    """Save the list of available banks to accounts.csv for a specific user."""
    try:
        temp_accounts = []
        updated = False
        
        # Convert list of dicts or strings to a pipe-separated string
        # Assuming banks_list might be [{"text": "Bank A", "value": "1"}, ...] or just list of names
        # We will store just the names for readability, or maybe Name:Value
        
        bank_names = []
        for b in banks_list:
            if isinstance(b, dict):
                bank_names.append(b.get("text", "").strip())
            else:
                bank_names.append(str(b).strip())
        
        banks_str = "|".join(bank_names)

        with open(ACCOUNTS_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            
            # Ensure 'Available Banks' column exists
            if "Available Banks" not in fieldnames:
                fieldnames.append("Available Banks")
            
            for row in reader:
                if row["Username"] == username:
                    row["Available Banks"] = banks_str
                    updated = True
                temp_accounts.append(row)
        
        if updated:
            with open(ACCOUNTS_FILE, mode='w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(temp_accounts)
            log(f"Updated available banks for {username}")
    except Exception as e:
        log(f"Error updating available banks in CSV: {e}")
