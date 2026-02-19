# IPO Applier Bot (Apify Actor)

This bot automatically checks for and applies to available IPOs on Meroshare.

## Features
- **Auto-Discovery**: Detects new IPOs automatically.
- **Auto-Apply**: Applies for specified accounts.
- **Smart Validation**: Checks for duplicate applications.
- **Apify Compatible**: Ready to deploy as an Apify Actor.

## Usage

### On Apify
1. Create a new Actor.
2. Connect this GitHub repository.
3. Configure `accounts` in the Input tab.

### Input Schema
```json
{
    "accounts": [
        {
            "name": "My Account",
            "username": "...",
            "password": "...",
            "crn": "...",
            "pin": "...",
            "dp_id": "...",
            "bank_name": "...",
            "active": true
        }
    ]
}
```

## Local Development
1. Install dependencies: `pip install -r requirements.txt`
2. Run: `python main.py`
