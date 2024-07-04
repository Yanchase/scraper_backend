from flask import Blueprint, Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import openai

bp = Blueprint("webgpt", __name__)
# 假设您已有 OpenAI API key
openai.api_key = "your-openai-api-key"


@bp.route("/analyze-customer", methods=["POST"])
def analyze_customer():
    url = request.json.get("url")
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")
        page_text = " ".join(soup.stripped_strings)

        gpt_response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Analyze the following text from a company website and determine if it fits the target customer profile for a business selling water level sensors. Text: {page_text}",
            max_tokens=150,
        )
        result = gpt_response.choices[0].text.strip()

        return jsonify({"url": url, "analysis": result})
    except Exception as e:
        return jsonify({"error": str(e)})
