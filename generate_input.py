import csv
import json
import os

CSV_FILE = r"C:\Users\purib\Desktop\ipo\windows_package\accounts.csv"
OUTPUT_FILE = r"C:\Users\purib\Desktop\ipo\windows_package\apify_version\apify_input.json"

def convert_csv_to_apify_input():
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found.")
        return

    input_data = {
        "accounts": []
    }

    try:
        with open(CSV_FILE, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic validation
                if not row.get("Username"):
                    continue
                
                # Map CSV columns to Input Schema
                account = {
                    "name": row.get("Name", row.get("Username")),
                    "username": row.get("Username", ""),
                    "password": row.get("Password", ""),
                    "crn": row.get("CRN", ""),
                    "pin": row.get("PIN", ""),
                    "dp_id": row.get("DP ID", ""),
                    "bank_name": row.get("Bank Name", ""),
                    "active": str(row.get("Active", "True")).lower() == "true",
                    "available_banks": row.get("Available Banks", "") # Optional, not in schema but useful if logic supports it
                }
                
                # Filter out empty keys if schema is strict, but schema allows these
                input_data["accounts"].append(account)
                
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(input_data, f, indent=4)
        
        print(f"Successfully created {OUTPUT_FILE} with {len(input_data['accounts'])} accounts.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    convert_csv_to_apify_input()
