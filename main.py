# TODO: Add a rubrics form to get a more objective rating
from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
import requests
import os

TMDB_API_KEY = os.environ.get('TMDB_API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///new-movies-collection.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.app_context().push()
db = SQLAlchemy(app)


class Movie(db.Model):
    """Headings for SQLAlchemy database"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(500), nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(500), nullable=False)


db.create_all()


class UpdateMovie(FlaskForm):
    """Form for updating the rating and review of a movie in database"""
    rating = StringField('You Rating Out Of 10')
    review = StringField('Your Review')
    submit = SubmitField('Done')


class AddMovie(FlaskForm):
    """Form for adding a movie to database"""
    title = StringField('Movie Title')
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    all_movies = Movie.query.order_by(Movie.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    return render_template('index.html', movies=all_movies)


@app.route("/edit", methods=['GET', 'POST'])
def edit():
    form = UpdateMovie()
    if form.validate_on_submit():
        # Update A Record By PRIMARY KEY
        movie_id = request.args.get('id')
        movie_selected = Movie.query.get(movie_id)
        movie_selected.rating = float(form.rating.data)
        movie_selected.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    movie_id = request.args.get('id')
    movie_selected = Movie.query.get(movie_id)
    return render_template('edit.html', form=form, movie=movie_selected)


@app.route('/delete')
def delete():
    # Delete A Particular Record By PRIMARY KEY
    movie_id = request.args.get('id')
    movie_to_delete = Movie.query.get(movie_id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        data = form.data
        title = data['title']
        data = requests.get(
            url=f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}'
                f'&query={title.replace(" ", "+") if " " in title else title}',
            params={"api_key": TMDB_API_KEY}
        ).json()['results']
        return render_template('select.html', titles=data)
    return render_template('add.html', form=form)


@app.route('/find')
def find():
    movie_id = request.args.get('id')
    movie = requests.get(url=f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}').json()
    new_movie = Movie(
        title=movie['title'],
        year=int(movie['release_date'].split('-')[0]),
        description=movie['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{movie['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit', id=new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)
