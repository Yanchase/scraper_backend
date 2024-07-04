from flask import Blueprint, request, jsonify, send_file
import csv
import os
import traceback
import requests
from bs4 import BeautifulSoup
import random

# Initialize the blueprint
bp = Blueprint("scrape", __name__)

# User agents list to mimic browser requests
user_agent = [
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; Acoo Browser 1.98.744; .NET CLR 3.5.30729)",
    "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; Acoo Browser 1.98.744; .NET CLR 3.5.30729)",
    "Mozilla/5.0 (compatible; MSIE 9.0; AOL 9.7; AOLBuild 4343.19; Windows NT 6.1; WOW64; Trident/5.0; FunWebProducts)",
    "Mozilla/5.0 (compatible; MSIE 9.0; AOL 9.1; AOLBuild 4334.5012; Windows NT 6.0; WOW64; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 9.0; AOL 9.0; Windows NT 6.0; Trident/5.0)",
    "Mozilla/5.0 (X11; U; UNICOS lcLinux; en-US) Gecko/20140730 (KHTML, like Gecko, Safari/419.3) Arora/0.8.0",
    "Mozilla/5.0 (X11; U; Linux; ru-RU) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6 (Change: 802 025a17d)",
    "Mozilla/5.0 (X11; U; Linux; pt-PT) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.4"
    "Mozilla/5.0 (X11; U; Linux; en-GB) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 239 52c6958)",
]


def scrape_data_yellowpage(url):
    headers = {"User-Agent": random.choice(user_agent)}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all("div", class_="MuiCard-root")
        data = []
        for listing in listings:
            title = (
                listing.find("h3", class_="MuiTypography-root").get_text(strip=True)
                if listing.find("h3", class_="MuiTypography-root")
                else "N/A"
            )
            phone = (
                listing.find("a", {"class": "MuiButtonBase-root"})["href"].split(":")[
                    -1
                ]
                if listing.find("a", {"class": "MuiButtonBase-root"})
                else "N/A"
            )
            link = (
                listing.find(
                    "a",
                    {
                        "class": "MuiButtonBase-root MuiButton-root MuiButton-text ButtonWebsite MuiButton-textSecondary MuiButton-fullWidth"
                    },
                )["href"]
                if listing.find(
                    "a",
                    {
                        "class": "MuiButtonBase-root MuiButton-root MuiButton-text ButtonWebsite MuiButton-textSecondary MuiButton-fullWidth"
                    },
                )
                else "N/A"
            )
            address = (
                listing.find("p", class_="MuiTypography-root").get_text(strip=True)
                if listing.find("p", class_="MuiTypography-root")
                else "N/A"
            )
            data.append([title, address, phone, link])
        return data
    else:
        return []


@bp.route("/", methods=["GET"])
def scrape():
    keyword = request.args.get("keyword", "Construction")
    file_name = f"{keyword}_data.csv"
    is_first_page = True
    start_page = int(request.args.get("start", 1))  # Default start page is 1
    end_page = int(request.args.get("end", 1))  # Default end page is 30
    try:
        for pageNum in range(start_page, end_page + 1):  # Adjustable page range
            url = f"https://www.yellowpages.com.au/search/listings?clue={keyword}&locationClue=All+States&pageNumber={pageNum}"
            data = scrape_data_yellowpage(url)
            if data:
                if len(data) > 3:
                    data = data[:-3]
                    write_to_csv_yp(file_name, data, is_first_page)
                    is_first_page = False
            else:
                print(f"No data found to write to CSV for page {pageNum}.")

        file_path = os.path.join(os.getcwd(), file_name)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return jsonify({"error": "File not found after creation attempt"}), 404

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def write_to_csv_yp(file_name, data, is_first_page):
    mode = "w" if is_first_page else "a"
    with open(file_name, mode=mode, newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_first_page:
            writer.writerow(["Title", "Address", "Phone", "Website"])
        for item in data:
            if item[3] != "N/A":  # Skip rows where website is "N/A"
                writer.writerow(item)


def scrape_data(url):
    headers = {"User-Agent": random.choice(user_agent)}
    response = requests.get(url, headers=headers, timeout=30)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        listings = soup.find_all(
            "div", class_="row"
        )  # Adjust class as per the HTML structure
        data = []
        for listing in listings:
            paragraph = (
                listing.find("p").get_text(strip=True) if listing.find("p") else "N/A"
            )
            link_element = listing.find("a", href=True)
            title = "N/A"  # Default value if no suitable link is found
            link = "N/A"  # Default value if no suitable link is found

            if link_element:
                link = link_element["href"]
                text = link_element.text.strip()
                if "Website" in text:
                    title = text.replace("Visit the ", "").replace(" Website", "")

            data.append([paragraph, title, link])
        return data
    else:
        print(f"Failed to retrieve data, status code: {response.status_code}")
        return []


def write_to_csv(
    file_name, data, headers=["Introduction", "Title", "Website"], is_first_page=True
):
    mode = "w" if is_first_page else "a"
    with open(file_name, mode, newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_first_page:
            writer.writerow(headers)
        for item in data:
            writer.writerow(item)


def remove_na_rows(file_path):
    cleaned_data = []
    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)
        cleaned_data.append(headers)
        for row in reader:
            if "N/A" not in row:
                cleaned_data.append(row)
    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerows(cleaned_data)


@bp.route("/monnit", methods=["GET"])
def main():
    file_name = "partner_link.csv"
    url = "https://www.monnit.com/partner/current-partners/"
    try:
        data = scrape_data(url)
        if data:
            write_to_csv(file_name, data)
            remove_na_rows(file_name)
            file_path = os.path.join(os.getcwd(), file_name)
            if os.path.exists(file_path):
                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({"error": "File not found after creation attempt"}), 404
        else:
            return jsonify({"error": "No data found to write to CSV"}), 404
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
