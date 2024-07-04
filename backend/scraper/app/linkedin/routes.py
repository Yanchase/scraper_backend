import csv
from io import StringIO
import os
from telnetlib import EC
import tempfile
from bs4 import BeautifulSoup
from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    send_from_directory,
    after_this_request,
)
from werkzeug.utils import secure_filename

from .Linkedin import LinkedIn
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

bp = Blueprint("linkedin", __name__)


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


@bp.route("/find", methods=["POST"])
def process_file():
    file = request.files["file"]
    if file:
        temp_output = tempfile.NamedTemporaryFile(mode="w+", delete=False)
        driver = setup_driver()
        login(driver)
        csv_reader = csv.reader(file.stream)
        csv_writer = csv.writer(temp_output)
        headers = next(csv_reader)
        if "Company URL" not in headers:
            headers.append("Company URL")
        csv_writer.writerow(headers)

        for row in csv_reader:
            company_name = row[1]
            search_company(driver, company_name)
            company_url = get_company_link(driver)
            row.append(company_url if company_url else "URL not found")
            csv_writer.writerow(row)

        driver.quit()
        temp_output.seek(0)
        temp_output.close()
        return send_file(
            temp_output.name,
            as_attachment=True,
            attachment_filename="processed_companies.csv",
        )
    else:
        return "No file provided", 400


@bp.route("/employee", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part", 400
    file = request.files["file"]
    if file.filename == "":
        return "No selected file", 400
    if file and allowed_file(file.filename):
        temp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        file.save(temp.name)

        # Define cleanup function to delete the file after sending it
        @after_this_request
        def cleanup(response):
            os.unlink(temp.name)
            return response

        # Process the file if needed
        process_file(temp.name)
        # Send the file back to the client
        return send_file(
            temp.name,
            as_attachment=True,
            attachment_filename="processed_emails.csv",
            mimetype="text/csv",
        )
    else:
        return "Invalid file", 400


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"csv"}


def process_file(filename):
    with open(filename, mode="r", encoding="utf-8") as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            company_name = row[1]
            company_link = row[4]
            domain = row[3].split(";")[0].strip()
            companyID = LinkedIn.get_company_id(company_link)
            if companyID:
                linkedin = LinkedIn()
                linkedin.paginate_results(companyID, company_name, domain)
