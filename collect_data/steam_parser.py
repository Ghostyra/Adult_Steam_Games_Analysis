import re
import csv
import threading
from bs4 import BeautifulSoup, Tag, ResultSet
from typing import List, Dict


def to_str_with_sep(arr: List[str], sep: str) -> str:
    return sep.join(str(x) for x in arr)


class SteamParser:
    def __init__(self) -> None:
        self.url: str = ""

    def set_url(self, url: str) -> None:
        self.url = url

    def parsing(self) -> None:
        from creating_soup import get_links

        links: List[str] = get_links(self.url)
        headers: List[str] = ["Title", "Release date", "Developer", "Publisher", "Reviews count",
                   "Reviews summary", "Positive percent", "Tags", "Price", "Languages", "Achievements count",
                   "Genres", "Steam categories", "Sys req"]

        with open("steam_data.csv", "w", encoding='utf-8', newline="\n") as f:
            writer: csv.writer = csv.writer(f)
            writer.writerow(headers)
            for link in links:
                row: List[str] = self.parse_data(link)
                if row:
                    writer.writerow(row)

    def parse_data(self, link: str) -> List[str]:
        from creating_soup import create_soup

        page_soup: BeautifulSoup = create_soup(link)

        # If game not released or game without 18+ warning
        if page_soup.find(attrs={"class": "not_yet"}):
            return 0
        elif not page_soup.find(attrs={'id': 'game_area_content_descriptors'}):
            return 0

        # Parse title
        title: str = page_soup.find("div", attrs={"class": "apphub_AppName"}).text

        # Get users review, date, devs and publisher block
        user_reviews: Tag = page_soup.find("div", attrs={"class": "user_reviews"})

        # Parse release date
        try:
            date: str = user_reviews.find("div", attrs={"class": "date"}).text
        except Exception:
            date: str = "-"

        # Parse devs and publisher
        dev_rows: ResultSet = user_reviews.find_all("div", attrs={"class": "dev_row"})
        dev: List[str] = [word.text for word in dev_rows[0].find_all("a")]
        try:
            publisher: List[str] = [word.text for word in dev_rows[1].find_all("a")]
        # No publisher
        except IndexError:
            publisher: str = "-"

        # Parse reviews count, text-value, percent of positive review
        review_spans: ResultSet = user_reviews.find("div", attrs={"class": "subtitle column all"}). \
            next_sibling.next_sibling.find_all("span")
        # For case when reviews not enough or they don`t exist
        if len(review_spans) == 2:
            reviews_count: str = re.findall(r"[0-9]", review_spans[0].text)[0]
            game_review_summary: str = "-"
            percent: str = "-"
        elif len(review_spans) == 0:
            reviews_count: str = "-"
            game_review_summary: str = "-"
            percent: str = "-"
        else:
            game_review_summary: str = review_spans[0].text.strip()
            reviews_count: str = review_spans[1].text.strip().strip("()")
            # Check for trash-span like span with *
            if review_spans[2].text == "*":
                percent: str = re.findall(r"[0-9]+%", review_spans[3].text)[0]
            else:
                try:
                    percent: str = re.findall(r"[0-9]+%", review_spans[2].text)[0]
                except IndexError:
                    reviews_count: str = re.findall(r"[0-9]", review_spans[0].text)[0]
                    game_review_summary: str = "-"
                    percent: str = "-"

        # Parse tags
        tags_panel: Tag = page_soup.find('div', attrs={'class': 'glance_tags popular_tags'})
        tags: List[str] = []
        for tag in tags_panel.find_all('a'):
            tags.append(tag.text.strip())

        # Get price block
        price_panel: ResultSet = page_soup.find_all("div", attrs={"class": "game_purchase_action"})

        # If game doesnt have price panel
        if not price_panel:
            return 0

        # Ignore demo
        demo_ver: Tag = page_soup.find("div", attrs={"class": "game_area_purchase_game demo_above_purchase"})
        if demo_ver:
            price_panel: str = price_panel[1]
        else:
            price_panel: str = price_panel[0]
        price_panel_discount: Tag = price_panel.find("div", attrs={"class": "discount_original_price"})
        # Parse original price, ignore discount
        if price_panel_discount:
            price: str = price_panel_discount.text
        else:
            try:
                price: str = price_panel.find("div", attrs={"class": "game_purchase_price price"}).text.strip()
            # Free-to-play - no price
            except AttributeError:
                price: str = "Free"

        # Parse languages
        languages_table: Tag = page_soup.find("table", attrs={"class": "game_language_options"})
        languages: List[str] = [re.sub(r"\s+", " ", lang.text).strip() for lang in
                     languages_table.find_all("td", attrs={"class": "ellipsis"})]

        # Parse achievements count if they are
        achievements_count: int = 0
        achievements_block: Tag = page_soup.find("div", attrs={"class": "communitylink_achievement_images"})
        if achievements_block:
            achievements_count = int(re.findall(r"\d+", achievements_block.previous_sibling.previous_sibling.text)[0])

        # Parse genres without devs and publisher in this block
        genres_table: Tag = page_soup.find("div", attrs={"class": "details_block"})
        for div in genres_table.find_all("div", attrs={"class": "dev_row"}):
            div.decompose()
        genres: List[str] = [genre.text for genre in genres_table.find_all("a")]

        # Parse game steam-categories
        categories_table: Tag = page_soup.find("div", attrs={"id": "category_block"})
        categories: List[str] = [re.sub(r"\s+", " ", a.text).strip() for a in
                      categories_table.find_all("a", attrs={"class": "name"})]
        # Check VR
        if page_soup.find("div", attrs={"class": "block_title vrsupport"}):
            categories.append("VR support")

        # System req
        sys_req: Tag = page_soup.find('div', attrs={'class': 'game_area_sys_req sysreq_content active'})
        sys_req_dict: Dict[str, str] = {}
        for ul in sys_req.find_all('ul', attrs={'class': 'bb_ul'}):
            for li in ul.find_all('li'):
                li_text: List[str] = li.text.split(':')
                try:
                    sys_req_dict[li_text[0].strip()] = li_text[1].strip()
                except IndexError:
                    # For x64-warning
                    sys_req_dict["OS req"] = li_text[0].strip()

        return [title, date, to_str_with_sep(dev, ","), to_str_with_sep(publisher, ","),
                reviews_count, game_review_summary, percent, tags, price, to_str_with_sep(languages, ","),
                achievements_count, to_str_with_sep(genres, ","), to_str_with_sep(categories, ","), sys_req_dict]
