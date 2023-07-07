import os
import json
import asyncio
import requests
from pyppeteer import launch
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()

class QuoteScraper:
    def __init__(self):
        self.url = os.environ.get('INPUT_URL')
        self.output_file = os.environ.get('OUTPUT_FILE')
        self.proxy = os.environ.get('PROXY')
        self.quotes = []

    async def scrape_quotes(self):
        page_num = 1
        browser = await launch()
        page = await browser.newPage()
        
        while self._has_next_page(1 if page_num == 1 else page_num - 1):
            print(f"Scraping page {page_num}...")
            await page.goto(f"{self.url}page/{page_num}")
            await page.waitForSelector('.quote')

            quotes = await page.querySelectorAll('.quote')
           
            for quote in quotes:
                text = await quote.querySelectorEval('.text', 'element => element.textContent')
                author = await quote.querySelectorEval('.author', 'element => element.textContent')
                tags = await quote.querySelectorAllEval('.tag', 'elements => elements.map(el => el.textContent)')
                self.quotes.append({"text": text.strip().replace("\u201c","").replace("\u201d",""), "by": author.strip(), "tags": [tag.strip() for tag in tags]})
                
            page_num += 1
              
        await browser.close()       

    def _has_next_page(self, page):
        response = self._get_page_response(page)
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            next_link = soup.find('li', class_='next')
            if next_link is None:
                return False
        return True

    def _get_page_response(self, page):
        if self.proxy:
            proxies = {
                'http': f"http://{self.proxy}",
                'https': f"http://{self.proxy}"
            }
            response = requests.get(f"{self.url}page/{page}", proxies=proxies)
        else:
            response = requests.get(f"{self.url}page/{page}")
        if response.status_code == 200:
            return response
        return None

    def save_quotes_to_file(self):
        with open(self.output_file, "w") as file:
            for quote in self.quotes:
                json.dump(quote, file)
                file.write("\n")

async def main():
    scraper = QuoteScraper()
    await scraper.scrape_quotes()
    scraper.save_quotes_to_file()

asyncio.get_event_loop().run_until_complete(main())
