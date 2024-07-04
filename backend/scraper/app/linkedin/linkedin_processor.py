from flask import Blueprint, Flask, request, send_file, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
import csv

from backend.scraper.app.linkedin.Linkedin import LinkedIn

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["ALLOWED_EXTENSIONS"] = {"csv"}

bp = Blueprint("linkedin", __name__)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in app.config["ALLOWED_EXTENSIONS"]
    )





if __name__ == "__main__":
    app.run(debug=True)
