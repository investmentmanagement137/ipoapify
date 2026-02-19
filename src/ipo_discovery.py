import asyncio
from config_and_utils import log

async def discover_available_ipos(page):
    log("Discovering available IPOs...")
    try:
        await page.goto("https://meroshare.cdsc.com.np/#/asba", wait_until="networkidle")
        # Ensure at least one Apply/Edit button or a container is present
        try:
            await page.wait_for_selector("button:has-text('Apply'), button:has-text('Edit')", timeout=15000)
        except:
            log("No Apply/Edit buttons appeared after timeout.")
            return []

        available_ipos = []
        buttons = await page.query_selector_all("button:has-text('Apply'), button:has-text('Edit')")
        log(f"Found {len(buttons)} entries on ASBA page.")
        
        for i in range(len(buttons)):
            current_btns = await page.query_selector_all("button:has-text('Apply'), button:has-text('Edit')")
            if i >= len(current_btns): 
                break
            btn = current_btns[i]
            
            # Identify company name before clicking
            try:
                # Use a single line JS string to avoid Python syntax errors with multi-line strings in evaluate
                js_code = "(btn) => { const row = btn.closest('tr') || btn.closest('.company-list') || btn.closest('.card'); return row ? row.innerText : ''; }"
                parent_row = await page.evaluate(js_code, btn)
                
                if parent_row:
                    company_name = parent_row.split("\n")[0].split("-")[0].strip()
                else:
                    company_name = f"IPO_Item_{i+1}"
            except:
                company_name = f"IPO_Item_{i+1}"

            if not company_name or company_name.lower() in ['apply', 'edit']:
                company_name = f"IPO_Item_{i+1}"

            log(f"Checking item: {company_name}")
            await btn.click()
            await asyncio.sleep(5)
            
            # Capture any URL that looks like an application page
            if "/asba/apply/" in page.url or "/asba/edit/" in page.url:
                available_ipos.append({"company": company_name, "url": page.url})
                log(f"Valid IPO Target Found: {company_name} -> {page.url}")
                await page.goto("https://meroshare.cdsc.com.np/#/asba")
                await asyncio.sleep(4)
                try:
                    await page.locator(".nav-link:has-text('Apply for Issue')").click()
                    await asyncio.sleep(3)
                except:
                    pass
            else:
                log(f"Clicked but didn't go to application page (URL: {page.url}). Ignoring.")

        return available_ipos
    except Exception as e:
        log(f"Discovery Error: {e}")
        return []
