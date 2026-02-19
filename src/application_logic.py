import asyncio
from config_and_utils import log, update_account_status
from history_tracker import save_completion

# Expert Playwright Helpers (inspired by playwright-skill)
async def safe_click(page, selector, timeout=15000, retries=2):
    for i in range(retries + 1):
        try:
            await page.wait_for_selector(selector, state="visible", timeout=timeout)
            await page.click(selector)
            return True
        except Exception as e:
            if i == retries:
                log(f"Final click failure on {selector}: {e}")
                return False
            log(f"Retry click on {selector} ({i+1}/{retries})...")
            await asyncio.sleep(2)

async def safe_fill(page, selector, value, timeout=15000):
    try:
        await page.wait_for_selector(selector, state="visible", timeout=timeout)
        await page.fill(selector, value)
        return True
    except Exception as e:
        log(f"Fill failure on {selector}: {e}")
        return False

async def setup_toast_monitor(page, account, company_name, boid, url):
    async def handle_toast(text):
        clean_text = text.strip()
        if not clean_text: return
        log(f"[{account['name']}] TOAST: {clean_text}")
        if "successfully" in clean_text.lower():
        if "successfully" in clean_text.lower():
            await save_completion(
                account['name'], 
                account['username'], 
                boid, 
                company_name, 
                url,
                crn=account.get('crn'),
                active=account.get('active', True),
                selected_bank=account.get('selected_bank_name'),
                available_banks=account.get('available_banks_list')
            )
            update_account_status(account['username'], "pin_correct", True)
        
        if "wrong transaction pin" in clean_text.lower():
            log(f"ALERT: Wrong PIN detected for {account['name']}")
            update_account_status(account['username'], "pin_correct", False)
    
    try: 
        await page.expose_function("reportToast", handle_toast)
    except: 
        pass 

    await page.evaluate("""
        if (window.toastObserver) window.toastObserver.disconnect();
        window.toastObserver = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === 1) {
                        const selector = '.toast-message, .toastr, [role="alert"]';
                        if (node.matches(selector)) window.reportToast(node.innerText);
                        node.querySelectorAll(selector).forEach(t => window.reportToast(t.innerText));
                    }
                }
            }
        });
        window.toastObserver.observe(document.body, { childList: true, subtree: true });
    """)

async def login(page, account):
    log(f"Logging in: {account['name']}")
    try:
        await page.goto("https://meroshare.cdsc.com.np/#/login", wait_until="networkidle")
        await page.wait_for_selector(".select2-selection--single")
        await page.click(".select2-selection--single")
        await page.wait_for_selector(".select2-search__field")
        await page.fill(".select2-search__field", account['dp_id'])
        await page.press(".select2-search__field", "Enter")
        await page.fill("#username", account['username'])
        await page.fill("#password", account['password'])
        await page.click("button.sign-in")
        
        # Wait for either Dashboard or an error message
        try:
            await page.wait_for_selector("a:has-text('Dashboard')", timeout=20000)
            log("Login OK.")
            update_account_status(account['username'], "credentials_correct", True)
            return True
        except:
            if "Dashboard" in (await page.content()):
                update_account_status(account['username'], "credentials_correct", True)
                return True
            log("Login Failed.")
            update_account_status(account['username'], "credentials_correct", False)
            return False
    except Exception as e:
        log(f"Login Error: {e}")
        return False

async def apply_process(page, account, ipo):
    log(f"Processing {ipo['company']} for {account['name']}...")
    try:
        # 1. Navigate to Application
        await page.goto(ipo['url'], wait_until="domcontentloaded")
        await asyncio.sleep(5)
        
        # Verify Navigation
        if "/asba/apply/" not in page.url and "/asba/edit/" not in page.url:
            log(f"Wrong page: {page.url}. Attempting manual navigation...")
            await page.goto("https://meroshare.cdsc.com.np/#/asba", wait_until="networkidle")
            # Search and click Apply
            rows = await page.query_selector_all("tr, .company-list")
            clicked = False
            for row in rows:
                if ipo['company'].lower() in (await row.inner_text()).lower():
                    btn = await row.query_selector("button:has-text('Apply'), button:has-text('Edit')")
                    if btn:
                        await btn.click()
                        await page.wait_for_load_state("networkidle")
                        clicked = True
                        break
            if not clicked or ("/asba/apply/" not in page.url and "/asba/edit/" not in page.url):
                log("Manual navigation failed. Skipping.")
                return

        # 2. Check State
        if "/asba/edit/" in page.url:
            log(f"{ipo['company']} already applied (Edit mode). Skipping.")
        if "/asba/edit/" in page.url:
            log(f"{ipo['company']} already applied (Edit mode). Skipping.")
            await save_completion(
                account['name'], 
                account['username'], 
                "", 
                ipo['company'], 
                ipo['url'],
                crn=account.get('crn'),
                active=account.get('active', True),
                selected_bank="Already Applied (N/A)",
                available_banks=[]
            )
            return
            return

        # 3. Bank and Account Selection
        log(f"Selecting Bank: {account['bank_name']}")
        try:
            await page.wait_for_selector("#selectBank", state="visible", timeout=20000)
            # Give it time for AJAX options
            await asyncio.sleep(3)
            
            options = await page.query_selector_all("#selectBank option")
            val = None
            valid_list = []
            for opt in options:
                v = await opt.get_attribute("value")
                t = (await opt.inner_text()).strip().replace("\n", " ").replace("\r", " ")
                if v:
                    safe_text = t.encode('ascii', 'ignore').decode('ascii')
            for opt in options:
                v = await opt.get_attribute("value")
                t = (await opt.inner_text()).strip().replace("\n", " ").replace("\r", " ")
                if v:
                    safe_text = t.encode('ascii', 'ignore').decode('ascii')
                    valid_list.append({"text": safe_text, "value": v})
            
            # Store for output
            account['available_banks_list'] = [b['text'] for b in valid_list]
            
            # Save banks to CSV
            from config_and_utils import save_account_banks
            save_account_banks(account['username'], valid_list)

            # Match Bank
            for item in valid_list:
                if account['bank_name'].lower() in item['text'].lower() or ("nic asia" in account['bank_name'].lower() and "nic asia" in item['text'].lower()):
                    val = item['value']
                if account['bank_name'].lower() in item['text'].lower() or ("nic asia" in account['bank_name'].lower() and "nic asia" in item['text'].lower()):
                    val = item['value']
                    log(f"Matched Bank: {item['text']}")
                    account['selected_bank_name'] = item['text']
                    break
            
            if not val and valid_list:
                val = valid_list[0]['value']
            if not val and valid_list:
                val = valid_list[0]['value']
                log(f"Fallback to first bank: {valid_list[0]['text']}")
                account['selected_bank_name'] = valid_list[0]['text']

            if val:
                await page.select_option("#selectBank", value=val)
                # Important: Trigger change event
                await page.evaluate("document.querySelector('#selectBank').dispatchEvent(new Event('change', { bubbles: true }))")
                
                # Wait for Account list
                log("Waiting for account list...")
                await asyncio.sleep(5)
                # Find the account dropdown (not selectBank)
                account_dropdown = page.locator("select:not(#selectBank)")
                await account_dropdown.wait_for(state="attached", timeout=15000)
                # Wait for at least one valid option
                await page.wait_for_selector("select:not(#selectBank) option[value]:not([value=''])", state="attached", timeout=10000)
                
                await account_dropdown.select_option(index=1)
                await page.evaluate("document.querySelector('select:not(#selectBank)').dispatchEvent(new Event('change', { bubbles: true }))")
                log("Account selected.")
            else:
                log("No banks found.")
                return
        except Exception as e:
            log(f"Selection Error: {e}")
            await page.screenshot(path=f"select_err_{account['username']}.png")
            return

        # 4. Fill Form
        log("Filling Form...")
        try:
            await safe_fill(page, "#appliedKitta", "10")
            await page.keyboard.press("Tab")
            await safe_fill(page, "#crnNumber", account['crn'])
            await page.click("#disclaimer", force=True)
            
            proceed_btn = page.locator("button:has-text('Proceed')")
            if await proceed_btn.is_enabled():
                await proceed_btn.click()
                await page.wait_for_selector("#transactionPIN", state="visible", timeout=10000)
                await page.fill("#transactionPIN", account['pin'])
                await page.click("button:has-text('Apply')")
                log("Application submitted. Waiting for confirmation...")
                await asyncio.sleep(8)
            else:
                log("Proceed button disabled. Check details.")
        except Exception as e:
            log(f"Form Error: {e}")
            await page.screenshot(path=f"form_err_{account['username']}.png")

    except Exception as e:
        log(f"Global App Error: {e}")
        await page.screenshot(path=f"global_err_{account['username']}.png")
