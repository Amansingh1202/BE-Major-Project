from flask import Flask, render_template, request
import pandas as pd
import requests
import json
import numpy as np
from flask_sqlalchemy import SQLAlchemy
import json

f = open(
    "./movies.json",
)
data = json.load(f)

url = "http://localhost:8501/v1/models/my_model:predict"

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///./database/database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

reviews = []


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/movie_page/<movie_id>")
def movie_page(movie_id):
    movie_data = {}
    for d in data["movies"]:
        if int(d["id"]) == int(movie_id):
            movie_data = d
    print(movie_data)
    return render_template("movie_page.htm", movie_data=movie_data)


@app.route("/sentiment_analysis", methods=["POST", "GET"])
def sentiment_analysis():
    if request.method == "POST":
        input = request.form.get("review")
        inputValue = [input]
        inputValues = pd.DataFrame(inputValue)
        print(inputValues)
        data = json.dumps(
            {
                "signature_name": "serving_default",
                "instances": inputValues.values.tolist(),
            }
        )
        print(data)
        headers = {"content-type": "application/json"}
        json_response = requests.post(url, data=data, headers=headers)
        output = json.loads(json_response.text)
        probability = np.squeeze(output["predictions"][0])
        print(probability)
        if probability < 0:
            review_result1 = 0
        elif probability >= 0:
            review_result1 = 1
        new_review = {"reviewData": input, "result": review_result1}
        reviews.append(new_review)
        return render_template(
            "index.html",
            reviews=reviews,
        )


if __name__ == "__main__":
    app.run(debug=True)