import asyncio,json
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True,args=['--enable-unsafe-swiftshader'])
  page=await browser.new_page();bad=[];errors=[]
  page.on('request',lambda r:bad.append(r.url) if '/api/region-image' in r.url or ':8000' in r.url else None)
  page.on('pageerror',lambda e:errors.append(str(e)))
  base='http://127.0.0.1:8080/github-pages/'
  await page.goto(base)
  await page.evaluate("async()=>{const m=await import('./resultados-python.js');await m.abrirComparaciones()}")
  await page.locator('#region-MOON').wait_for(state='visible')
  print('main panels:',await page.locator('#region-MOON option').count(),await page.locator('#region-MARS option').count())
  for body,region in [('MOON','MOON:12671'),('MARS','MARS:124')]:
   await page.goto(base+f'recursos/comparador_imagenes/index.html?body={body}&region={region}&embed=1')
   await page.locator('#comparison').wait_for(state='visible',timeout=30000)
   print('static image:',await page.locator('#planet-tag').inner_text())
  await page.goto(base+'recursos/catalogo_regiones/index.html?body=MARS')
  await page.locator('a[href*="comparador_imagenes"]').first.wait_for()
  assert not bad,bad
  assert not errors,errors
  print('PASS: subdirectory, main panels, lunar and martian images, catalogue; zero backend calls; zero JS errors')
  await browser.close()
asyncio.run(main())
