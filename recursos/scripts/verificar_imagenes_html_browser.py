import asyncio,json
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',headless=True)
  page=await b.new_page();api=[]
  async def deny(route):api.append(route.request.url);await route.abort()
  await page.route('**/api/region-image**',deny)
  await page.goto('http://127.0.0.1:8080/github-pages/recursos/comparador_imagenes/index.html?body=MOON&embed=1')
  await page.locator('#comparison').wait_for(state='visible',timeout=30000)
  result=await page.evaluate('''async()=>{
   const manifest=await (await fetch('./regiones_manifest.json')).json();
   const summary=await (await fetch('../comparacion_tacana/similitud_catalogo_resumen.json')).json();
   const ids=[...new Set(Object.values(summary.selections).flatMap(s=>[s.selected_region,...s.matching_regions.map(r=>r.region)]))];
   const failed=[];let loaded=0;
   for(let i=0;i<ids.length;i+=8){await Promise.all(ids.slice(i,i+8).map(async id=>{
    try{const entry=manifest.regions[id];if(!entry.metadata)throw Error('missing metadata');
     const response=await fetch(entry.metadata);if(!response.ok)throw Error('metadata HTTP '+response.status);
     const data=await response.json();const img=new Image();img.src=data.file;await img.decode();if(!img.naturalWidth)throw Error('empty image');loaded++;
    }catch(e){failed.push({id,error:e.message})}
   }));}
   return {expected:ids.length,loaded,failed};
  }''')
  print(json.dumps(result),flush=True)
  assert result['expected']==196 and result['loaded']==196 and not result['failed']
  assert not api,api
  print('PASS: all 196 images decoded in browser, zero image API calls',flush=True)
  await b.close()
asyncio.run(main())
