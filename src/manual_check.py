import asyncio
import traceback
from playwright.async_api import async_playwright
from config_and_utils import ACCOUNTS, log
from application_logic import login
from ipo_discovery import discover_available_ipos

async def run_check():
    log("=== Checking for Available IPOs ===")
    
    active_accounts = [a for a in ACCOUNTS if a.get("active", True)]
    if not active_accounts:
        log("No active accounts found in accounts.csv")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=800)
        context = await browser.new_context()
        page = await context.new_page()

        log(f"Logging in with {active_accounts[0]['name']}...")
        if await login(page, active_accounts[0]):
            available_ipos = await discover_available_ipos(page)
            
            if available_ipos:
                print("\n" + "="*50)
                print(f"{'Company Name':<30} | {'URL'}")
                print("-" * 50)
                for ipo in available_ipos:
                    print(f"{ipo['company']:<30} | {ipo['url']}")
                print("="*50 + "\n")
            else:
                log("No available IPOs found.")
        else:
            log("Login failed during check.")

        await browser.close()
        log("=== Check Finished ===")

if __name__ == "__main__":
    try:
        asyncio.run(run_check())
    except Exception:
        log(f"CRASH: {traceback.format_exc()}")
