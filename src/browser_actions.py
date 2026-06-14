import asyncio

async def send_key(tab, key, code, key_code):
    import zendriver.cdp.input_ as inp
    await tab.send(inp.dispatch_key_event(type_="keyDown", key=key, code=code, windows_virtual_key_code=key_code, native_virtual_key_code=key_code))
    await asyncio.sleep(0.005)
    await tab.send(inp.dispatch_key_event(type_="keyUp", key=key, code=code, windows_virtual_key_code=key_code, native_virtual_key_code=key_code))
    await asyncio.sleep(0.005)

async def type_text(tab, text):
    import zendriver.cdp.input_ as inp
    for char in str(text):
        await tab.send(inp.dispatch_key_event(type_="char", text=char))
        await asyncio.sleep(0.005)

async def visual_click(tab, element):
    if not element:
        return False
    try:
        await tab.evaluate("""(el) => {
            el.scrollIntoView({behavior:'smooth',block:'center'});
            el.style.outline='3px solid #7289da';
            el.style.boxShadow='0 0 15px #7289da';
            setTimeout(()=>{el.style.outline='';el.style.boxShadow='';},500);
        }""", element)
        await asyncio.sleep(0.1)
        await element.mouse_click()
        return True
    except:
        try:
            await element.click()
            return True
        except:
            return False

async def select_month(tab, month):
    for attempt in range(3):
        clicked = await tab.evaluate("""(() => {
            const btn = document.querySelector('div[aria-label="Month"]');
            if (btn) {
                btn.scrollIntoView({block: 'center'});
                setTimeout(() => btn.click(), 50);
                return true;
            }
            return false;
        })()""")
        
        if not clicked:
            await asyncio.sleep(0.3)
            continue
        
        await asyncio.sleep(0.4)
        await type_text(tab, month)
        await asyncio.sleep(0.15)
        await send_key(tab, "Enter", "Enter", 13)
        await asyncio.sleep(0.2)
        
        verified = await tab.evaluate("""(() => {
            const btn = document.querySelector('div[aria-label="Month"]');
            if (btn) {
                const text = (btn.innerText || btn.textContent || '').trim().toLowerCase();
                return text.length > 0;
            }
            return false;
        })()""")
        
        if verified:
            return True
        
        await send_key(tab, "Escape", "Escape", 27)
        await asyncio.sleep(0.2)
    
    return False

async def select_day(tab, day):
    for attempt in range(3):
        clicked = await tab.evaluate("""(() => {
            const btn = document.querySelector('div[aria-label="Day"]');
            if (btn) {
                btn.scrollIntoView({block: 'center'});
                setTimeout(() => btn.click(), 50);
                return true;
            }
            return false;
        })()""")
        
        if not clicked:
            await asyncio.sleep(0.3)
            continue
        
        await asyncio.sleep(0.4)
        await type_text(tab, str(day))
        await asyncio.sleep(0.15)
        await send_key(tab, "Enter", "Enter", 13)
        await asyncio.sleep(0.2)
        
        verified = await tab.evaluate("""(() => {
            const btn = document.querySelector('div[aria-label="Day"]');
            if (btn) {
                const text = (btn.innerText || btn.textContent || '').trim();
                return text.length > 0;
            }
            return false;
        })()""")
        
        if verified:
            return True
        
        await send_key(tab, "Escape", "Escape", 27)
        await asyncio.sleep(0.2)
    
    return False

async def select_year(tab, year):
    target_year = int(year)
    
    for attempt in range(3):
        opened = await tab.evaluate("""(() => {
            const btn = document.querySelector('div[aria-label="Year"]');
            if (btn) {
                btn.scrollIntoView({block: 'center'});
                setTimeout(() => btn.click(), 50);
                return true;
            }
            return false;
        })()""")
        
        if not opened:
            await asyncio.sleep(0.3)
            continue
        
        await asyncio.sleep(0.6)
        
        await send_key(tab, "End", "End", 35)
        await asyncio.sleep(0.10)
        
        presses_needed = 2023 - target_year
        
        if presses_needed > 0:
            for _ in range(min(presses_needed, 130)):
                await send_key(tab, "ArrowUp", "ArrowUp", 38)
                await asyncio.sleep(0.025)
        
        await asyncio.sleep(0.2)
        
        await send_key(tab, "Enter", "Enter", 13)
        await asyncio.sleep(0.3)
        
        verified = await tab.evaluate(f"""(() => {{
            const btn = document.querySelector('div[aria-label="Year"]');
            if (btn) {{
                const text = (btn.innerText || btn.textContent || '').trim();
                return text.length > 0;
            }}
            return false;
        }})()""")
        
        if verified:
            return True
        
        await send_key(tab, "Escape", "Escape", 27)
        await asyncio.sleep(0.2)
    
    return False
