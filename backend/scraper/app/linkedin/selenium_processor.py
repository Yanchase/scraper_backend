import csv
import logging
from logging.handlers import RotatingFileHandler
from .selenium_setup import setup_driver, login, search_company, get_company_link
import tempfile


def setup_logging():
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = RotatingFileHandler("application.log", backupCount=3)
    log_handler.setFormatter(log_format)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)


setup_logging()


def start_scraper(filepath):
    driver = setup_driver()
    login(driver)

    temp_file = tempfile.NamedTemporaryFile(
        delete=False, suffix=".csv", mode="w+", newline="", dir="/tmp"
    )
    temp_file_path = temp_file.name

    with open(filepath, "r", newline="") as file, open(
        temp_file_path, "w", newline=""
    ) as outfile:
        csv_reader = csv.reader(file)
        csv_writer = csv.writer(outfile)
        headers = next(csv_reader)
        if "Company URL" not in headers:
            headers.append("Company URL")
        csv_writer.writerow(headers)

        for row in csv_reader:
            company_name = row[1]
            search_company(driver, company_name)
            company_url = get_company_link(driver)
            logging.info(f"Company: {company_name}, URL: {company_url}")
            row.append(company_url if company_url else "URL not found")
            logging.warning(f"Writing row: {row}")
            csv_writer.writerow(row)

    driver.quit()
    return temp_file_path
