import asyncio,os,json
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True,args=['--enable-unsafe-swiftshader'])
  page=await b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto('http://127.0.0.1:8080/github-pages/')
  await page.wait_for_function("document.querySelectorAll('.sismo-icon').length===42",timeout=60000)
  assert await page.locator('.sismo-marker:visible').count()==0,'markers visible at country zoom'
  await page.locator('.tacana-map-label').click()
  await page.locator('#alternar-sismos').click()
  await page.wait_for_timeout(1500)
  for x in await page.locator('.comparison-close').all():
   if await x.is_visible():await x.click()
  await page.wait_for_timeout(500)
  target=None
  for marker in await page.locator('.sismo-icon').all():
   if await marker.evaluate('(e)=>{const r=e.getBoundingClientRect();return r.top>100&&r.bottom<innerHeight-50&&r.left>100&&r.right<innerWidth-100&&e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}'):
    target=marker;break
  assert target,'no reachable earthquake marker'
  await target.hover();await page.wait_for_timeout(1200)
  tip=page.locator('.sismo-tooltip:popover-open')
  await tip.wait_for(state='visible',timeout=5000)
  print('tooltip:',await tip.inner_text())
  await tip.hover();assert await tip.is_visible()
  await page.keyboard.press('Escape');await page.wait_for_timeout(200);assert await page.locator('.sismo-tooltip:popover-open').count()==0
  await target.focus();await page.wait_for_timeout(1000);assert await page.locator('.sismo-tooltip:popover-open').count()==1
  await page.screenshot(path=str(Path(os.environ['TEMP'])/'sismos-tacana.png'))
  for _ in range(6):
   await page.locator('.maplibregl-ctrl-zoom-out').click()
   await page.wait_for_timeout(350)
  assert await page.locator('.sismo-marker:visible').count()==0,'markers remain after zooming out'
  assert await page.locator('.sismo-tooltip:popover-open').count()==0
  print('PASS: 42 markers, hover, hoverable tooltip, Escape, keyboard focus; JS errors:',errors)
  assert not errors
  await b.close()
asyncio.run(main())
