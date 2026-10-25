import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from psycopg.errors import UniqueViolation

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


@app.route("/", methods=["GET", "POST"])
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
    with get_database_connection() as connection:
        deleted_genre = connection.execute(
            "DELETE FROM public.genres WHERE id = %s RETURNING name",
            (genre_id,),
        ).fetchone()

    if deleted_genre is None:
        flash("That genre was not found.", "error")
    else:
        flash(f"Removed {deleted_genre[0]}.", "success")

    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)
