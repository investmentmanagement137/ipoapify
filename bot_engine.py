import asyncio
import traceback
from playwright.async_api import async_playwright
from config_and_utils import ACCOUNTS, log
from history_tracker import is_already_completed
from ipo_discovery import discover_available_ipos
from application_logic import login, apply_process, setup_toast_monitor

if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    args = parser.parse_args()
    
    # We need to pass the headless argument to the main function or modify main to accept it using a global or partial
    # Since main() takes no arguments currently, let's modify it to accept headless
    
    # Redefine main to accept headless
    async def main(headless=False):
        log("=== Meroshare Bot Started (Modular) ===")
        if headless:
            log("Running in HEADLESS mode.")
        
        # Filter active accounts
        active_accounts = [a for a in ACCOUNTS if a.get("active", True)]
        if not active_accounts:
            log("No active accounts found in accounts.csv")
            return

        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=headless, slow_mo=800)
            context = await browser.new_context()
            page = await context.new_page()

            # 1. Use the first account to discover available IPOs
            log(f"Using {active_accounts[0]['name']} to check for available IPOs...")
            if not await login(page, active_accounts[0]):
                log("Initial login failed. Cannot proceed to discovery.")
                await browser.close()
                return

            available_ipos = await discover_available_ipos(page)
            
            if not available_ipos:
                log("No available IPOs found or error during discovery.")
                await browser.close()
                return

            # 2. Iterate through all active accounts and apply if not already completed
            for acc in active_accounts:
                # Check history for each available IPO for this account
                to_do = [ipo for ipo in available_ipos if not is_already_completed(acc['username'], ipo['company'])]
                
                if not to_do:
                    log(f"All available IPOs already applied for {acc['name']}. Skipping.")
                    continue

                log(f"Processing {len(to_do)} IPOs for {acc['name']}...")

                # If it's not the first account, we need to login again
                if acc != active_accounts[0]:
                    await context.close()
                    context = await browser.new_context()
                    page = await context.new_page()
                    if not await login(page, acc):
                        log(f"Login failed for {acc['name']}. Skipping.")
                        continue

                for ipo in to_do:
                    # Setup monitoring for success messages
                    await setup_toast_monitor(page, acc, ipo['company'], "", ipo['url'])
                    
                    # Perform application
                    await apply_process(page, acc, ipo)
                    await asyncio.sleep(2)

            await browser.close()
            log("=== Meroshare Bot Finished ===")

    try:
        asyncio.run(main(headless=args.headless))
    except Exception:
        log(f"CRASH: {traceback.format_exc()}")
        sys.exit(1) # Exit with error code on crash
