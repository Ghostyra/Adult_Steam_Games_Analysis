import time
import requests
from requests import Response
from typing import List
from bs4 import BeautifulSoup, Tag
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Get all game-links from the page
def get_links(url: str) -> List[str]:
    driver: webdriver.Chrome = webdriver.Chrome('chromedriver.exe')
    driver.get(url)

    # Wait new window in browser
    try:
        WebDriverWait(driver, 10000).until(EC.number_of_windows_to_be(2))
    finally:
        pass

    len_page: int = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0,document.body.scrollHeight)")
        new_len_page: int = len(driver.page_source)
        time.sleep(2)
        if new_len_page == len_page:
            break
        len_page = new_len_page

    links: List[str] = []
    soup: BeautifulSoup = BeautifulSoup(driver.page_source, "html.parser")
    driver.close()

    div: Tag = soup.find("div", attrs={"id": "search_resultsRows"})
    for a in div.find_all("a"):
        link: str = a.get("href")
        # Verify that is no bundle
        if "/sub/" in link:
            continue
        links.append(link)

    return links


# Create soup for parsing
def create_soup(url: str) -> BeautifulSoup:
    response: Response = requests.get(url)
    response.encoding = 'utf-8'
    soup: BeautifulSoup = BeautifulSoup(response.text, "html.parser")
    return soup
