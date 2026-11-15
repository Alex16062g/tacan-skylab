import asyncio, json, os
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True,args=['--enable-unsafe-swiftshader'])
        page=await browser.new_page(viewport={'width':1200,'height':900})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        for body,region in [('MOON','MOON:12671'),('MARS','MARS:4453')]:
            await page.goto(f'http://127.0.0.1:8000/recursos/comparador_imagenes/index.html?body={body}&region={region}&embed=1')
            await page.locator('#comparison').wait_for(state='visible',timeout=120000)
            print(json.dumps({'region':region,'label':await page.locator('#planet-tag').inner_text(),'image':await page.locator('#planet').evaluate('(e)=>[e.complete,e.naturalWidth,e.naturalHeight]'),'controls':await page.locator('.image-view-controls').inner_text(),'errors':errors},ensure_ascii=True),flush=True)
        await page.screenshot(path=str(Path(os.environ['TEMP'])/'catalogue-imagery-check.png'))
        response=await page.request.get('http://127.0.0.1:8000/api/region-image?body=MOON&region=INVALID')
        assert response.status==422
        await page.goto('http://127.0.0.1:8000/recursos/catalogo_regiones/index.html?body=MOON')
        await page.locator('a[href*="comparador_imagenes"]').first.wait_for(timeout=30000)
        print('catalogue image links:',await page.locator('a[href*="comparador_imagenes"]').count())
        await browser.close()
asyncio.run(main())
