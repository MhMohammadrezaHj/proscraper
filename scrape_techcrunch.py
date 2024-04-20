import time
import os

from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TechCrunchScraper:
    HTML_FOLDER_PATH = "/Users/hadi/Documents/workspace/daneshkar/week 11 (project sraping)/scraped_html"

    MODE = "normal"  # or headless
    BLOCK_IMAGES = True
    BLOCK_JS = False
    DRIVER_PATH = "/Users/hadi/Documents/workspace/daneshkar/week 11 (project sraping)/shared/selenium/chromedriver"
    WEBSITE_MAIN_PAGE = "https://techcrunch.com"
    current_category_scraping_name = ""

    def __init__(self, mode="normal", block_images=True, block_js=False) -> None:
        self.MODE = mode
        self.BLOCK_IMAGES = block_images
        self.BLOCK_JS = block_js

        self.driver = None
        self.service = None
        self.all_categories_list = None

    def run_driver(self, page_load_timeout=20):
        if self.driver is not None:
            return
        if self.MODE == "headless":
            options = webdriver.ChromeOptions()
            options.headless = True
            options.add_argument("--window-size=1920,1200")
            options.add_argument('--no-sandbox')         
            options.add_argument('--disable-dev-shm-usage')   
        elif self.MODE == "normal":
            options = webdriver.ChromeOptions()

        if self.BLOCK_IMAGES or self.BLOCK_JS:
            ### This blocks images and javascript requests
            block_dict = {}
            if self.BLOCK_IMAGES:
                block_dict["images"] = 2
            if self.BLOCK_JS:
                block_dict["javascript"] = 2
            chrome_prefs = {"profile.default_content_setting_values": block_dict}
            options.experimental_options["prefs"] = chrome_prefs

        self.service = Service(executable_path=self.DRIVER_PATH)
        self.driver = webdriver.Chrome(service=self.service, options=options)
        self.driver.set_page_load_timeout(page_load_timeout)
        return self.driver

    def open_link_in_driver(self, link):  # , try_again_if_timeout=True):
        if self.driver is None:
            self.run_driver()
        # while True:
        try:
            self.driver.get(link)
        except TimeoutException:
            pass
            # if try_again_if_timeout:
            #     continue
            # else:
            # break

    def scroll_to_bottom(self):
        while True:
            try:
                javaScript = "window.scrollBy(0, 100000);"
                self.driver.execute_script(javaScript)
                return
            except:
                continue

    def get_list_of_all_categories(self):
        if self.all_categories_list is not None:
            return self.all_categories_list

        self.open_link_in_driver(
            self.WEBSITE_MAIN_PAGE
        )  # , try_again_if_timeout=False)
        categories_links_path = '//header[contains(@class, "site-navigation")]//ul[contains(@class, "menu")]/li[@class="menu__item"]/a'

        try:
            WebDriverWait(self.driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, categories_links_path))
            )
        except:
            WebDriverWait(self.driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, categories_links_path))
            )

        categories_links = self.driver.find_elements(By.XPATH, categories_links_path)
        main_categories_list = [
            (link.get_attribute("href"), link.text)
            for link in categories_links
            if "/category/" in link.get_attribute("href")
        ]
        more_categories_btn = '//header[contains(@class, "site-navigation")]//ul[contains(@class, "menu")]/li[@class="menu__item more-link"]/a'
        more_btn = self.driver.find_element(By.XPATH, more_categories_btn)
        more_btn.click()

        more_categories_links_path = '//header[contains(@class, "site-navigation")]//div[@class="desktop-nav navigation-desktop__flyout"]//li[@class="menu__item"]/a'
        more_categories_links = self.driver.find_elements(
            By.XPATH, more_categories_links_path
        )
        more_categories_list = [
            (link.get_attribute("href"), link.text)
            for link in more_categories_links
            if "/category/" in link.get_attribute("href")
        ]

        all_categories_list = main_categories_list + more_categories_list
        self.all_categories_list = all_categories_list
        return self.all_categories_list

    def get_article_data_from_html(self, article_header):
        def get_article_header_type():
            try:
                article_category = article_header.find_element(
                    By.XPATH, './div[@class="article__primary-category"]/a'
                )
                return {
                    "type": types["article_category"],
                    "text": article_category.text,
                    "href": article_category.get_attribute("href"),
                }
            except:
                try:
                    article_label = article_header.find_element(
                        By.XPATH,
                        './div[@class="featured-article__label"]/div[contains(@class, "featured-article__label__text")]',
                    )
                    return {
                        "type": types["article_label"],
                        "text": article_label.text,
                        "href": article_label.get_attribute("href"),
                    }
                except:
                    article_event_title = article_header.find_element(
                        By.XPATH, './h3[@class="article__event-title"]/a'
                    )
                    return {
                        "type": types["article_event"],
                        "text": article_event_title.text,
                        "href": article_event_title.get_attribute("href"),
                    }

        types = {
            "article_category": "Category",
            "article_label": "Label",
            "article_event": "Event",
        }
        title = article_header.find_element(
            By.XPATH, './h2[@class="post-block__title"]'
        ).text
        # //div[contains(@class, "river")]/div//article/header//div[@class="post-block__meta"]//span[@class="river-byline__authors"]//a
        author_name_el = article_header.find_element(
            By.XPATH,
            './/div[@class="post-block__meta"]//span[@class="river-byline__authors"]//a',
        )
        author_name, author_link = author_name_el.text, author_name_el.get_attribute(
            "href"
        )
        # //div[contains(@class, "river")]/div//article/header//div[@class="post-block__meta"]//span[@class="river-byline__full-date-time__wrapper"]//time
        date_and_time = article_header.find_element(
            By.XPATH,
            './/div[@class="post-block__meta"]//div[@class="river-byline__full-date-time__wrapper"]//time',
        ).get_attribute("datetime")
        article_canonical_link = article_header.find_element(
            By.XPATH, './h2[@class="post-block__title"]/a'
        ).get_attribute("href")
        return {
            "title": title,
            "article_link": article_canonical_link,
            "header": get_article_header_type(),
            "author_name": author_name,
            "author_link": author_link,
            "date_and_time": date_and_time,
        }

    def scrape_new_articles_of_category_link(
        self, category_page_link, already_scraped_articles_num=0
    ):
        if already_scraped_articles_num == 0:
            self.open_link_in_driver(category_page_link)
        else:
            self.scroll_to_bottom()

        load_more_btn_xpath = (
            '//*[@id="tc-main-content"]//button[contains(@class, "load-more")]'
        )
        try:
            WebDriverWait(self.driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, load_more_btn_xpath))
            )
            time.sleep(5)
        except:
            WebDriverWait(self.driver, 1000).until(
                EC.element_to_be_clickable((By.XPATH, load_more_btn_xpath))
            )

        category_river_div_path = '//div[contains(@class, "river")]/div'
        time.sleep(10)
        river_div = self.driver.find_element(By.XPATH, category_river_div_path)
        articles_elements = river_div.find_elements(By.XPATH, "//article")
        print(f'{already_scraped_articles_num-40 if already_scraped_articles_num >= 40 else 0}:')
        articles_elements = articles_elements[already_scraped_articles_num-40 if already_scraped_articles_num >= 40 else 0:]
        for article in articles_elements:
            article_header = article.find_element(By.XPATH, "./header")
            self.save_article_data_in_database(
                self.get_article_data_from_html(article_header)
            )

    def click_load_more_in_category_page(self, wait_after=10, try_until_success=True):
        while True:
            try:
                time.sleep(wait_after)
                load_more_btn_xpath = (
                    '//*[@id="tc-main-content"]//button[contains(@class, "load-more")]'
                )
                load_more_btn = self.driver.find_element(By.XPATH, load_more_btn_xpath)
                load_more_btn.click()
                return
            except:
                if try_until_success:
                    continue
                break

    def get_number_of_current_articles_in_page(self):
        category_river_div_path = '//div[contains(@class, "river")]/div'
        river_div = self.driver.find_element(By.XPATH, category_river_div_path)
        articles_elements = river_div.find_elements(By.XPATH, "//article")
        return len(articles_elements)

    def scrape_category_scroll_down(self, category_link):
        already_scraped_articles_num = 0
        while True:
            if already_scraped_articles_num > 1400:
                self.scrape_new_articles_of_category_link(
                    category_link, already_scraped_articles_num
                )
            if already_scraped_articles_num == 0:
                self.open_link_in_driver(category_link)
            else:
                self.scroll_to_bottom()
            already_scraped_articles_num = self.get_number_of_current_articles_in_page()
            print(already_scraped_articles_num)
            self.scroll_to_bottom()
            self.click_load_more_in_category_page(try_until_success=True)

    def save_article_data_in_database(self, article_data):
        # {
        #     'title': title,
        #     'article_link': article_canonical_link,
        #     'header': get_article_header_type(),get_number_of_current_articles_in_page
        #     'author_name': author_name,
        #     'author_link': author_link,
        #     'date_and_time': date_and_time,
        # }
        from app_database import save_article_data_to_database

        article = save_article_data_to_database(
            article_data["article_link"],
            article_data["author_name"],
            article_data["author_link"],
            article_data["header"]["href"],
            article_data["title"],
        )
        if article:
            until_num = self.get_number_of_current_articles_in_page()
            category_slug = article.category.slug
            file_name = (
                f"category_{self.current_category_scraping_name}_{until_num:05}.html"
            )
            self.save_html_of_page(file_name)
            # article.set_scarping_html_backup_name(file_name)
            article.save()

    def save_html_of_page(self, file_name: str):
        # category_startups_20
        file_name = file_name.lower()
        html_path = os.path.join(self.HTML_FOLDER_PATH, file_name)
        #######
        # import os
        # file_name = 'category_startups_00100.html'
        # HTML_FOLDER_PATH = "/Users/hadi/Documents/workspace/daneshkar/week 11 (project sraping)/scraped_html"
        # list_of_present_files = [file for file in os.listdir(HTML_FOLDER_PATH)]
        # for present_file_name in list_of_present_files:
        #     if present_file_name.replace('.html', '').split('_')[-1] < file_name.replace('.html', '').split('_')[-1]:
        #         print('x')
        #         print(present_file_name.replace('.html', '').replace('category_', '').split('_')[-1], file_name.replace('.html', '').replace('category_', '').split('_')[-1])
        #         if present_file_name.replace('.html', '').replace('category_', '').split('_')[-1] < file_name.replace('.html', '').replace('category_', '').split('_')[-1]:
        #             print(os.path.join(HTML_FOLDER_PATH, present_file_name))
        #             os.remove(os.path.join(HTML_FOLDER_PATH, present_file_name))
        #######
        list_of_present_files = [file for file in os.listdir(self.HTML_FOLDER_PATH)]
        for present_file_name in list_of_present_files:
            if (
                present_file_name.replace(".html", "").split("_")[-1]
                < file_name.replace(".html", "").split("_")[-1]
            ):
                if (
                    present_file_name.replace(".html", "")
                    .replace("category_", "")
                    .split("_")[-1]
                    < file_name.replace(".html", "")
                    .replace("category_", "")
                    .split("_")[-1]
                ):
                    os.remove(os.path.join(self.HTML_FOLDER_PATH, present_file_name))
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        return present_file_name

    def start_scraping(self):
        self.run_driver()
        self.get_list_of_all_categories()
        for category_link, category_name in self.all_categories_list:
            self.current_category_scraping_name = category_name
            self.scrape_category_scroll_down(category_link)


scraper = TechCrunchScraper()
scraper.open_link_in_driver("https://techcrunch.com/")
scraper.start_scraping()
