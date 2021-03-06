from flask import render_template, request
import pandas as pd
import requests
import numpy as np
import model
import demoji
import csv
import json
from __init__ import app
import logging
from autocorrect import Speller

spell = Speller(lang='en')

# Creating a slang dictionary from doc file
slang_data = []
with open("slang_dict.doc", "r") as exRtFile:
    exchReader = csv.reader(exRtFile, delimiter="`", quoting=csv.QUOTE_NONE)
    for row in exchReader:
        slang_data.append(row)
slang_dict = {}
for word in slang_data:
    if len(word) >= 2:
        slang_dict[word[0]] = word[1]


log = logging.getLogger("werkzeug")
log.setLevel(logging.ERROR)

f = open(
    "../movies.json",
)

movie_data_json = json.load(f)

url = "http://localhost:8501/v1/models/my_model:predict"


# new_value = ( (old_value - old_min) / (old_max - old_min) ) * (new_max - new_min) + new_min
def convert_range(val):
    if val == 0:
        return 0
    new_value = ((val - (-1)) / (1 - (-1))) * (5 - 0) + 0
    return round(new_value)


@app.route("/")
def home():
    movies = model.Movie.query.all()
    # Finds top 5 Movies with highest average score from the database
    top_movies = (
        model.Movie.query.order_by(model.Movie.average_score.desc()).limit(5).all()
    )
    top_movies_src = []
    for movie in top_movies:
        src_val = "../static/images/movie" + str(movie.id) + ".jpg"
        top_movies_src.append(src_val)
    movie_scores = []
    for mov in movies:
        movie_scores.append(mov.average_score)
    score_new = []
    for score in movie_scores:
        score_new.append(convert_range(score))
    return render_template(
        "index.html", scores=score_new, top_movies_src=top_movies_src
    )


@app.route("/movie_page/<movie_id>")
def movie_page(movie_id):
    reviews = model.Comments.query.filter_by(movie_id=movie_id).all()
    movie_data = {}
    for d in movie_data_json["movies"]:
        if int(d["id"]) == int(movie_id):
            movie_data = d
    return render_template("movie_page.htm", movie_data=movie_data, reviews=reviews)


@app.route("/sentiment_analysis/<movie_id>", methods=["POST", "GET"])
def sentiment_analysis(movie_id):
    if request.method == "POST":
        movie_data = {}
        for d in movie_data_json["movies"]:
            if int(d["id"]) == int(movie_id):
                movie_data = d
        inputV = request.form.get("review")
        input1 = inputV
        inputV = demoji.replace_with_desc(inputV, ":").replace(":", "")
        vb = inputV.split(" ")
        for w in range(len(vb)):
            if vb[w] in slang_dict:
                vb[w] = slang_dict[vb[w]]
        inputV = " ".join(vb)
        words = inputV.split(" ")
        words1 = []
        for w in words:
            words1.append(spell(w))
        inputV = " ".join(words1)
        inputValue = [inputV]
        inputValues = pd.DataFrame(inputValue)
        data = json.dumps(
            {
                "signature_name": "serving_default",
                "instances": inputValues.values.tolist(),
            }
        )
        headers = {"content-type": "application/json"}
        json_response = requests.post(url, data=data, headers=headers)
        output = json.loads(json_response.text)
        probability = np.squeeze(output["predictions"][0])
        if probability < 0:
            review_result1 = 0
        elif probability >= 0:
            review_result1 = 1
        new_review = {"reviewData": input1, "result": review_result1}
        movie = model.Movie.query.filter_by(id=movie_id).first()
        new_review = model.Comments(
            comment=input1, review_status=review_result1, movie_id=movie_id
        )
        movie.average_score = movie.average_score + probability
        model.db.session.add(new_review)
        model.db.session.commit()
        reviews = model.Comments.query.filter_by(movie_id=movie_id).all()
        return render_template(
            "movie_page.htm",
            movie_data=movie_data,
            reviews=reviews,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True, threaded=True)
