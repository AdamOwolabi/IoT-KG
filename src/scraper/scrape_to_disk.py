"""
Scrape each URL in urls using selectors from the chosen config and
write extracted fields to JSON files on disk for downstream LLM use.

Args:
    urls(list[str]): List of URLs to scrape
    config(str): Name of the config to use

Example Command:
  uv run -m src.scraper.scrape_to_disk --amazon
"""

import os
import json
import asyncio
import datetime
import argparse

from src.configs.amazon import AMAZON_SELECTOR
from src.configs.walmart import WALMART_SELECTOR

from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# TODO: Have this read from a file of urls
URLS = [
    "https://www.amazon.com/Apple-Watch-Smartwatch-Aluminum-Always/dp/B0FQF5BZ8Z/ref=sr_1_1_sspa?crid=3I8DRUBPXFK9O&dib=eyJ2IjoiMSJ9.rbA7sWhkavB3MiJI2T1Bw_HFqMsDD9VhwQXIYNa3HNJrEWEZOnae9x0wLm1eZuzrM-r1OfE5A0KLtDYohfEqau5QWpUhalwGv_jPMLdcspuqUXSQew1DML6iuhwrw_kHb9f59Ail-l0Txp4dagTzxq448ye0QhANKAck0HCPdZXkVIF2dFbsjzoPwNtBanFZq42FdDjIMrOzWPdSlJmDBAhniT6U7YNmFsp6ouqpeGE.x9hoR0h3WkixJFZadTN5b2EoYmuPRCalh4DkNvgvcdM&dib_tag=se&keywords=apple%2Bwatch&qid=1759442529&sprefix=apple%2Bwatch%2Caps%2C124&sr=8-1-spons&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1",
    'https://www.amazon.com/Amazon-vibrant-helpful-routines-Charcoal/dp/B09B8V1LZ3/ref=sr_1_1?crid=1FILQKC6UQ9B5&dib=eyJ2IjoiMSJ9.z0kBrN5J4yDwE3Z69yvpFvmwHHypkHHD1EEB0Tq7d-twKIMmrd6CdpzAKHt3QwCIqpCGWOtUGso25ArgjUeQiby0wRAtPziXyEv_Tf6qw3ScIhyK8WiI5tvRhkwcaZAYJpqeIDTu_m3cf2k1gyY2IF6h7Q-TpQpXqLkVlwxHcP1Ckn7GRQitYbsIXzmMdVt_vBDTTWAeeARk7Yo7VrzCI4_YLLlMbjp_5sTMWrY7dRA.M_EhWcOAkjfHtGyy6bJoS1n8Dh5KYN-aTbt1Uez3DW0&dib_tag=se&keywords=echo%2Bdot&qid=1759097324&sprefix=echo%2Bdo%2Cspecialty-aps%2C87&sr=8-1-catcorr&srs=17938598011&ufe=app_do%3Aamzn1.fos.74097168-0c10-4b8a-b96b-8388a1a12daf&th=1' 
]

CONFIGS = {
    "amazon": AMAZON_SELECTOR,
    "walmart": WALMART_SELECTOR
}

async def scrape_to_disk(urls: list[str], config: str):
    async with Stealth().use_async(async_playwright()) as p:
            browser = None
            try:
                browser = await p.firefox.launch(headless=False)
                output_dir = f"src/data/html_dumps/{config}"
                os.makedirs(output_dir, exist_ok=True)

                for url in urls:
                    page = await browser.new_page()
                    try:
                        await page.goto(url, wait_until='domcontentloaded')
                        await page.wait_for_timeout(5000)

                        print(f"Scraping {url} using {config} config")

                        result = {"url": url}
                        for key, value in CONFIGS[config].items():
                            result[key] = await page.locator(value).inner_text()

                        with open(f"{output_dir}/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", "w", encoding="utf-8") as f:
                            f.write(json.dumps(result, indent=2))
                    finally:
                        await page.close()
            except Exception as e:
                raise Exception("Error scraping to disk: ", e)
            finally:
                await browser.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scrape e-commerce websites')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--amazon', action='store_true', help='Use Amazon config')
    group.add_argument('--walmart', action='store_true', help='Use Walmart config')

    args = parser.parse_args()
    
    if args.amazon:
        config = "amazon"
    elif args.walmart:
        config = "walmart"
    
    asyncio.run(scrape_to_disk(URLS, config))