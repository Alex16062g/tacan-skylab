"""Verify language switching without navigation or changes to scientific results."""
import argparse
import asyncio
import json
import os
from pathlib import Path

from playwright.async_api import async_playwright


async def verify(base):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path='C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
            headless=True, args=['--enable-unsafe-swiftshader'])
        context = await browser.new_context(viewport={'width': 1440, 'height': 1000})
        page = await context.new_page()
        errors, backend = [], []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('request', lambda request: backend.append(request.url)
                if '/api/region-image' in request.url else None)
        await page.goto(base)
        await page.locator('.tacana-map-label:enabled').wait_for(timeout=45000)
        assert await page.locator('html').get_attribute('lang') == 'en'
        assert await page.locator('[data-language=en]').get_attribute('aria-pressed') == 'true'
        await page.locator('.tacana-map-label').click()
        await page.locator('#region-MOON').wait_for()
        assert await page.locator('#region-MOON option').count() == 195
        assert await page.locator('#region-MARS option').count() == 1
        await page.locator('#region-MOON').select_option(index=1)
        region = await page.locator('#region-MOON').input_value()
        scores = await page.locator('.similarity-score').all_text_contents()
        await page.wait_for_timeout(1200)
        await page.evaluate('window.languageNavigationSentinel = 42')
        await page.locator('[data-language=es]').focus()
        await page.keyboard.press('Enter')
        assert await page.locator('html').get_attribute('lang') == 'es'
        assert await page.locator('#region-MOON').input_value() == region
        assert await page.locator('.similarity-score').all_text_contents() == scores
        assert await page.evaluate('window.languageNavigationSentinel') == 42
        assert 'Pendiente' in await page.locator('#comparison-MARS').inner_text()
        assert await page.locator('.maplibregl-ctrl-zoom-in').get_attribute('aria-label') == 'Acercar'
        assert await page.locator('#alternar-sismos').get_attribute('aria-pressed') == 'false'
        await page.wait_for_function("document.querySelectorAll('.sismo-icon').length === 42")
        assert 'Magnitud' in await page.locator('.sismo-tooltip').first.text_content()
        await page.locator('[data-language=en]').click()
        assert 'Magnitude' in await page.locator('.sismo-tooltip').first.text_content()
        await page.locator('.comparison-image-button').first.click()
        frame = page.frame_locator('#image-comparison-dialog iframe')
        await frame.locator('#comparison').wait_for(timeout=30000)
        assert 'Note:' in await frame.locator('#imagery-note').inner_text()
        image_url = await frame.locator('#planet').get_attribute('src')
        await page.evaluate("async () => (await import('./idiomas/i18n.js')).setLanguage('es')")
        await frame.locator('html[lang=es]').wait_for()
        assert 'Nota:' in await frame.locator('#imagery-note').inner_text()
        assert 'Recuperado' in await frame.locator('.embedded-sources').inner_text()
        assert await frame.locator('#planet').get_attribute('src') == image_url
        await page.locator('#image-comparison-dialog button').click()
        await page.reload()
        assert await page.locator('html').get_attribute('lang') == 'es'

        routes = [
            ('recursos/catalogo_regiones/index.html?body=MARS', '#rows tr', 'Catálogo', 'catalog'),
            ('recursos/catalogo_regiones/condiciones.html?body=MARS&region=MARS:4475', '#content', 'Condiciones', 'Conditions'),
            ('recursos/comparacion_tacana/ambiente.html?body=MARS', '#content', 'Ambiente', 'Environment'),
            ('recursos/comparador_3d/index.html?body=MOON', '#reference canvas', 'en 3D', 'in 3D'),
            ('recursos/comparador_imagenes/index.html?body=MARS&region=MARS:4475', '#comparison', 'comparación', 'comparison'),
        ]
        for route, ready, spanish, english in routes:
            await page.goto(base + route)
            await page.locator(ready).first.wait_for(timeout=30000)
            assert spanish in await page.title(), (route, await page.title())
            await page.locator('[data-language=en]').click()
            assert english in await page.title(), (route, await page.title())
            assert await page.locator('html').get_attribute('lang') == 'en'
            await page.locator('[data-language=es]').click()

        await page.goto(base + 'recursos/comparador_imagenes/index.html?body=MOON&region=MOON:9340')
        await page.locator('#retry').wait_for()
        assert 'pendiente' in await page.locator('#status').inner_text()
        await page.locator('[data-language=en]').click()
        assert 'pending' in await page.locator('#status').inner_text()

        await page.goto(base)
        for width in [390, 320]:
            await page.set_viewport_size({'width': width, 'height': 844})
            for language in ['es', 'en']:
                await page.locator(f'[data-language={language}]').click()
                assert await page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                bounds = await page.locator('.language-switch').bounding_box()
                assert bounds['x'] >= 0 and bounds['x'] + bounds['width'] <= width
        await page.screenshot(path=str(Path(os.environ['TEMP']) / 'tacana-language-mobile.png'))

        blocked = await browser.new_context()
        await blocked.add_init_script("Object.defineProperty(window, 'localStorage', {get() {throw new DOMException('Blocked', 'SecurityError')}})")
        tab = await blocked.new_page()
        await tab.goto(base)
        await tab.locator('[data-language=es]').click()
        assert await tab.locator('html').get_attribute('lang') == 'es'
        assert not errors, errors
        assert not backend, backend
        print(json.dumps({'passed': True, 'default': 'en', 'regions_unchanged': True,
                          'iframe_sync': True, 'persistence': True, 'blocked_storage': True,
                          'mobile_widths': [390, 320], 'secondary_pages': len(routes),
                          'javascript_errors': errors, 'backend_calls': backend}))
        await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--base', default='http://127.0.0.1:8080/github-pages/')
    asyncio.run(verify(parser.parse_args().base.rstrip('/') + '/'))
