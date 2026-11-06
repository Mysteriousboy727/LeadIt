import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=False)
        page = await br.new_page()
        await page.goto("https://www.google.com/maps/search/soap+in+Bengaluru", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        for t in ("Accept all", "Reject all"):
            b = page.get_by_role("button", name=t)
            if await b.count():
                await b.first.click()
                await page.wait_for_timeout(3000)
                break
        print("URL:", page.url)
        print("listings visible:", await page.locator("a.hfpxzc").count())
        await page.wait_for_timeout(4000)
        await br.close()

asyncio.run(main())
