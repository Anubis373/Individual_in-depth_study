import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg.errors import ForeignKeyViolation, UniqueViolation

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY") or os.urandom(32)


def get_database_connection():
    password = os.getenv("pg_password")
    if not password:
        raise RuntimeError("Set pg_password in the project .env file.")

    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=int(os.getenv("PGPORT", "5432")),
        dbname=os.getenv("PGDATABASE", "library_db"),
        user=os.getenv("PGUSER", "postgres"),
        password=password,
    )


@app.get("/")
def home():
    return redirect(url_for("books"))


@app.route("/genre", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a genre name.", "error")
            return redirect(url_for("index"))

        try:
            with get_database_connection() as connection:
                connection.execute(
                    "INSERT INTO public.genres (name) VALUES (%s)",
                    (name,),
                )
        except UniqueViolation:
            flash("That genre already exists.", "error")
        else:
            flash("Genre added.", "success")

        return redirect(url_for("index"))

    with get_database_connection() as connection:
        genres = connection.execute(
            "SELECT id, name FROM public.genres ORDER BY name"
        ).fetchall()

    return render_template("index.html", genres=genres)


@app.post("/genres/<int:genre_id>/delete")
def delete_genre(genre_id):
    try:
        with get_database_connection() as connection:
            deleted_genre = connection.execute(
                "DELETE FROM public.genres WHERE id = %s RETURNING name",
                (genre_id,),
            ).fetchone()
    except ForeignKeyViolation:
        flash("Remove this genre from its books before deleting it.", "error")
        return redirect(url_for("index"))

    if deleted_genre is None:
        flash("That genre was not found.", "error")
    else:
        flash(f"Removed {deleted_genre[0]}.", "success")

    return redirect(url_for("index"))


@app.get("/books")
def books():
    with get_database_connection() as connection:
        book_list = connection.execute(
            """
            SELECT books.id, books.title, books.author, genres.name
            FROM public.books
            JOIN public.genres ON genres.id = books.genre_id
            ORDER BY books.title, books.author
            """
        ).fetchall()

    return render_template("books.html", books=book_list)


@app.route("/books/add", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        genre_id_value = request.form.get("genre_id", "")

        if not title or not author:
            flash("Please enter both a title and an author.", "error")
            return redirect(url_for("add_book"))

        try:
            genre_id = int(genre_id_value)
        except ValueError:
            flash("Please select a valid genre.", "error")
            return redirect(url_for("add_book"))

        try:
            with get_database_connection() as connection:
                connection.execute(
                    """
                    INSERT INTO public.books (title, author, genre_id)
                    VALUES (%s, %s, %s)
                    """,
                    (title, author, genre_id),
                )
        except ForeignKeyViolation:
            flash("That genre no longer exists. Please select another one.", "error")
            return redirect(url_for("add_book"))

        flash("Book added.", "success")
        return redirect(url_for("books"))

    with get_database_connection() as connection:
        genres = connection.execute(
            "SELECT id, name FROM public.genres ORDER BY name"
        ).fetchall()

    return render_template("add_book.html", genres=genres)


@app.post("/books/<int:book_id>/delete")
def delete_book(book_id):
    with get_database_connection() as connection:
        deleted_book = connection.execute(
            "DELETE FROM public.books WHERE id = %s RETURNING title",
            (book_id,),
        ).fetchone()

    if deleted_book is None:
        flash("That book was not found.", "error")
    else:
        flash(f"Removed {deleted_book[0]}.", "success")

    return redirect(url_for("books"))


if __name__ == "__main__":
    app.run(debug=False)
