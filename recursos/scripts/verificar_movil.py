"""Check mobile map, comparison panels and image dialog without changing results."""
import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

async def main():
 async with async_playwright() as p:
  browser = await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', args=['--enable-unsafe-swiftshader'])
  context = await browser.new_context(viewport={'width':390,'height':844}, has_touch=True, is_mobile=True)
  page = await context.new_page()
  errors = []
  page.on('pageerror', lambda error: errors.append(str(error)))
  await page.goto('http://127.0.0.1:8080/github-pages/')
  await page.locator('.tacana-map-label:enabled').click(timeout=45000)
  await page.locator('#region-MOON').wait_for()
  scores = await page.locator('.similarity-score').all_text_contents()
  for width,height in [(320,568),(390,844),(844,390),(768,1024)]:
   await page.set_viewport_size({'width':width,'height':height})
   await page.wait_for_timeout(300)
   assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (width,'overflow')
   rects = await page.locator('.planet-map-preview').evaluate_all('(els)=>els.map(e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,w:r.width,b:r.bottom}})')
   assert all(r['w'] >= width-30 for r in rects), rects
   assert rects[1]['y'] >= rects[0]['b'], rects
   for selector in ['#region-MOON','#region-MARS']:
    await page.locator(selector).scroll_into_view_if_needed()
    assert await page.locator(selector).evaluate('(e)=>{const r=e.getBoundingClientRect();return e===document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)}')
   await page.locator('.comparison-image-button').first.click()
   frame = page.frame_locator('#image-comparison-dialog iframe')
   await frame.locator('#comparison').wait_for(timeout=30000)
   close = page.locator('#image-comparison-dialog button')
   box = await close.bounding_box()
   assert box['y'] >= 0 and box['y']+box['height'] <= height
   assert await frame.locator('html').evaluate('(e)=>e.scrollWidth <= innerWidth')
   await frame.locator('#swipe').focus()
   before = await frame.locator('#swipe').input_value()
   await page.keyboard.press('ArrowRight')
   assert await frame.locator('#swipe').input_value() != before
   await close.click()
   assert await page.locator('.similarity-score').all_text_contents() == scores
  await page.set_viewport_size({'width':390,'height':844})
  await page.locator('.planet-map-previews').scroll_into_view_if_needed()
  await page.screenshot(path=str(Path(os.environ['TEMP'])/'skylab-mobile-panels.png'))
  await page.locator('.comparison-close').first.click()
  assert await page.locator('.planet-map-previews').is_hidden()
  await page.set_viewport_size({'width':1440,'height':1000})
  await page.locator('.tacana-map-label').click()
  boxes = [await e.bounding_box() for e in await page.locator('.planet-map-preview').all()]
  assert boxes[0]['x'] > boxes[1]['x'] and abs(boxes[0]['y']-boxes[1]['y']) < 2
  assert not errors, errors
  await browser.close()
  print('Mobile: 320, 390, 768 and landscape 844; panels, selectors, modal, slider keyboard, close and desktop placement OK')

if __name__ == '__main__':
 asyncio.run(main())
