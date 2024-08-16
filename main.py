import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import requests
import bs4 as bs
import urllib.request

# Load the NLP model and TFIDF vectorizer from disk
filename = 'Preprocessing/nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('Preprocessing/tranform.pkl', 'rb'))

app = Flask(__name__)

def create_similarity():
    try:
        data = pd.read_csv('datasets/main_data.csv')
        cv = CountVectorizer()
        count_matrix = cv.fit_transform(data['comb'])
        similarity = cosine_similarity(count_matrix)
        return data, similarity
    except Exception as e:
        print("Error in creating similarity matrix:", e)
        return None, None

def rcmd(m):
    try:
        m = m.lower()
        data, similarity = create_similarity()
        if data is None or similarity is None:
            return 'Error in loading data. Please try again later.'
        
        if m not in data['movie_title'].unique():
            return 'Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies'
        else:
            i = data.loc[data['movie_title'] == m].index[0]
            lst = list(enumerate(similarity[i]))
            lst = sorted(lst, key=lambda x: x[1], reverse=True)
            lst = lst[1:11]
            l = [data['movie_title'][item[0]] for item in lst]
            return l
    except Exception as e:
        print("Error in recommending movie:", e)
        return 'Error in recommending movie. Please try again later.'

def convert_to_list(my_list):
    try:
        my_list = my_list.strip('[]').split('","')
        my_list = [item.strip('"') for item in my_list]
        return my_list
    except Exception as e:
        print("Error in converting to list:", e)
        return []

def get_suggestions():
    try:
        data = pd.read_csv('datasets/main_data.csv')
        return list(data['movie_title'].str.capitalize())
    except Exception as e:
        print("Error in getting suggestions:", e)
        return []

@app.route("/")
@app.route("/home")
def home():
    try:
        suggestions = get_suggestions()
        return render_template('home.html', suggestions=suggestions)
    except Exception as e:
        print("Error in loading home page:", e)
        return 'Error in loading home page. Please try again later.'

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.form
        title = data['title']
        cast_ids = convert_to_list(data['cast_ids'])
        cast_names = convert_to_list(data['cast_names'])
        cast_chars = convert_to_list(data['cast_chars'])
        cast_bdays = convert_to_list(data['cast_bdays'])
        cast_bios = convert_to_list(data['cast_bios'])
        cast_places = convert_to_list(data['cast_places'])
        cast_profiles = convert_to_list(data['cast_profiles'])
        imdb_id = data['imdb_id']
        poster = data['poster']
        genres = data['genres']
        overview = data['overview']
        vote_average = data['rating']
        vote_count = data['vote_count']
        release_date = data['release_date']
        runtime = data['runtime']
        status = data['status']
        rec_movies = convert_to_list(data['rec_movies'])
        rec_posters = convert_to_list(data['rec_posters'])

        suggestions = get_suggestions()

        movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}
        casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}
        cast_details = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

        sauce = urllib.request.urlopen(f'https://www.imdb.com/title/{imdb_id}/reviews?ref_=tt_ov_rt').read()
        soup = bs.BeautifulSoup(sauce, 'lxml')
        soup_result = soup.find_all("div", {"class": "text show-more__control"})

        reviews_list = []
        reviews_status = []
        for reviews in soup_result:
            if reviews.string:
                reviews_list.append(reviews.string)
                movie_review_list = np.array([reviews.string])
                movie_vector = vectorizer.transform(movie_review_list)
                pred = clf.predict(movie_vector)
                reviews_status.append('Good' if pred else 'Bad')

        movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

        return render_template('recommend.html', title=title, poster=poster, overview=overview, vote_average=vote_average,
                               vote_count=vote_count, release_date=release_date, runtime=runtime, status=status, genres=genres,
                               movie_cards=movie_cards, reviews=movie_reviews, casts=casts, cast_details=cast_details)
    except Exception as e:
        print("Error in recommending movie:", e)
        return 'Error in recommending movie. Please try again later.'

if __name__ == '__main__':
    app.run(debug=True)
