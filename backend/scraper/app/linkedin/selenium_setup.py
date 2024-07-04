from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

import logging

from logging.handlers import RotatingFileHandler


def setup_logging():
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = RotatingFileHandler("application.log", backupCount=3)
    log_handler.setFormatter(log_format)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)


setup_logging()


def setup_driver():
    service = Service("/Users/winwin/Documents/repository/geckodriver/geckodriver")
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(service=service, options=options)
    return driver


def login(driver):
    driver.get("https://www.linkedin.com")
    wait = WebDriverWait(driver, 8)
    with open(
        "/Users/winwin/Documents/GitHub/scraper_e/backend/scraper/config.txt", "r"
    ) as file:
        lines = file.readlines()
        username = lines[0].strip()
        password = lines[1].strip()

    username_input = wait.until(
        EC.visibility_of_element_located((By.ID, "session_key"))
    )
    password_input = wait.until(
        EC.visibility_of_element_located((By.ID, "session_password"))
    )
    username_input.send_keys(username)
    password_input.send_keys(password)
    password_input.send_keys(Keys.RETURN)


def search_company(driver, company_name):
    logging.debug(f"Searching for company: {company_name}")
    WebDriverWait(driver, 8).until(
        EC.visibility_of_element_located(
            (By.CSS_SELECTOR, "input.search-global-typeahead__input")
        )
    ).send_keys(company_name + Keys.RETURN)
    driver.get(
        f"https://www.linkedin.com/search/results/companies/?keywords={company_name}"
    )
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "a.app-aware-link"))
    ).click()


def get_company_link(driver):
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    company_list = soup.find("ul", {"class": "reusable-search__entity-result-list"})
    if not company_list:
        logging.error("No company list found.")
        return None
    links = company_list.find_all("a", {"class": "app-aware-link"})
    if not links:
        logging.debug("No links found.")
        return None
    return links[0]["href"]
