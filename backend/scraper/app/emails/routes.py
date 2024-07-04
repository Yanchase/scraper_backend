import random
import re
from flask import Blueprint, Response, request, jsonify, send_file
import csv
import asyncio
from bs4 import BeautifulSoup
import aiohttp
import logging
from io import BytesIO, StringIO
from stream_handler import DynamicStreamHandler

# Initialize the blueprint
bp = Blueprint("emails", __name__)
# Configure logging
import logging
from logging.handlers import RotatingFileHandler


# Setup logging
def setup_logging():
    log_format = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    log_handler = RotatingFileHandler("application.log", backupCount=3)
    log_handler.setFormatter(log_format)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(log_handler)


setup_logging()

stream_handler = DynamicStreamHandler()
logger = logging.getLogger("emails")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
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


async def find_contact_page(session, base_url, retries=3, timeout=5):
    headers = {"User-Agent": random.choice(user_agent)}
    known_contact_urls = [
        base_url.rstrip("/") + "/contact",
        base_url.rstrip("/") + "/contactus",
        base_url.rstrip("/") + "/contact-us",
        base_url.rstrip("/") + "/contact_us",
        base_url.rstrip("/") + "/store/contact_us",
    ]
    for url in known_contact_urls:
        for attempt in range(retries):
            try:
                async with session.get(
                    url, headers=headers, timeout=timeout
                ) as response:
                    if response.status == 200:
                        logger.debug(f"Contact page found: {url}")
                        return url
            except Exception as e:
                logger.error(f"Error accessing {url}: {str(e)}")
                if attempt < retries - 1:
                    logger.warning(f"Retrying {url} - Attempt {attempt + 1}")
                    await asyncio.sleep(2**attempt)
    logger.info(f"No contact page found for {base_url}")
    return None


async def extract_emails(session, url, timeout=5):
    headers = {"User-Agent": random.choice(user_agent)}
    if not url:
        logger.info(f"No URL provided for email extraction")
        return ""
    try:
        async with session.get(url, headers=headers, timeout=timeout) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                emails = re.findall(
                    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", soup.text
                )
                logger.info(f"Emails extracted from {url}: {emails}")
                return "; ".join(set(emails))
    except Exception as e:
        logger.error(f"Error extracting emails from {url}: {str(e)}")
    return ""


@bp.route("/find", methods=["POST"])
async def process_emails():
    file = request.files["file"]
    if not file:
        return jsonify({"status": "error", "message": "No file provided"}), 400

    input_stream = StringIO(file.stream.read().decode("utf-8"))
    csv_reader = csv.reader(input_stream)
    headers = next(csv_reader)
    try:
        lowercase_headers = [header.lower() for header in headers]
        website_index = lowercase_headers.index("website")
    except ValueError:
        return jsonify({"status": "error", "message": "No 'website' column found"}), 400

    if "Emails" not in headers:
        headers.append("Emails")

    updates = []
    # Prepare output using StringIO to capture CSV data
    output = StringIO()
    csv_writer = csv.writer(output)
    csv_writer.writerow(headers)

    async with aiohttp.ClientSession() as session:
        for row in csv_reader:
            website = row[website_index]
            contact_url = await find_contact_page(session, website)
            emails_primary = await extract_emails(session, website)
            emails_contact = (
                await extract_emails(session, contact_url) if contact_url else ""
            )
            emails = emails_primary or emails_contact
            row.append(emails)
            csv_writer.writerow(row)
            updates.append(f"Processed {website}: Emails found - {emails}")

    # Convert StringIO data to BytesIO for binary transmission
    output_binary_stream = BytesIO(output.getvalue().encode("utf-8"))
    output_binary_stream.seek(0)  # Ensure the stream is at the start

    return send_file(
        output_binary_stream,
        as_attachment=True,
        attachment_filename="processed_emails.csv",
        mimetype="text/csv",
    )


@bp.route("/stream_logs")
def stream_logs():
    level_name = request.args.get("level", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    queue = stream_handler.register_subscriber(level)
    return stream_handler.stream_logs(queue)


# Ensure the blueprint route registration is correct
bp.route("/find", methods=["POST"])(process_emails)
