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


@app.get("/genre")
def index():
    with get_database_connection() as connection:
        genres = connection.execute(
            "SELECT id, name FROM public.genres ORDER BY name"
        ).fetchall()

    return render_template("index.html", genres=genres)


@app.route("/genre/add", methods=["GET", "POST"])
def add_genre():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a genre name.", "error")
            return redirect(url_for("add_genre"))

        try:
            with get_database_connection() as connection:
                connection.execute(
                    "INSERT INTO public.genres (name) VALUES (%s)",
                    (name,),
                )
        except UniqueViolation:
            flash("That genre already exists.", "error")
            return redirect(url_for("add_genre"))

        flash("Genre added.", "success")
        return redirect(url_for("index"))

    return render_template("add_genre.html")


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
    title_filter = request.args.get("title", "").strip()
    author_filter = request.args.get("author", "").strip()
    genre_filter = request.args.get("genre_id", "").strip()
    selected_genre_id = None

    if genre_filter:
        try:
            selected_genre_id = int(genre_filter)
            if selected_genre_id < 1:
                raise ValueError
        except ValueError:
            flash("Please select a valid genre filter.", "error")
            return redirect(
                url_for("books", title=title_filter, author=author_filter)
            )

    filters = []
    parameters = []
    if title_filter:
        filters.append("books.title ILIKE %s")
        parameters.append(f"%{title_filter}%")
    if author_filter:
        filters.append("books.author ILIKE %s")
        parameters.append(f"%{author_filter}%")
    if selected_genre_id is not None:
        filters.append("books.genre_id = %s")
        parameters.append(selected_genre_id)

    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""

    with get_database_connection() as connection:
        genres = connection.execute(
            "SELECT id, name FROM public.genres ORDER BY name"
        ).fetchall()
        book_list = connection.execute(
            f"""
            SELECT books.id, books.title, books.author, genres.name
            FROM public.books
            JOIN public.genres ON genres.id = books.genre_id
            {where_clause}
            ORDER BY books.title, books.author
            """,
            parameters,
        ).fetchall()

    has_filters = bool(title_filter or author_filter or selected_genre_id)
    return render_template(
        "books.html",
        books=book_list,
        genres=genres,
        title_filter=title_filter,
        author_filter=author_filter,
        selected_genre_id=selected_genre_id,
        has_filters=has_filters,
    )


@app.get("/loans")
def loans():
    with get_database_connection() as connection:
        loan_list = connection.execute(
            """
            SELECT loans.id, books.title, books.author, genres.name,
                   loans.borrower_name, loans.loaned_on, loans.due_date,
                   loans.returned_on
            FROM public.loans AS loans
            JOIN public.books AS books ON books.id = loans.book_id
            JOIN public.genres AS genres ON genres.id = books.genre_id
            ORDER BY loans.returned_on NULLS FIRST, loans.loaned_on DESC, loans.id DESC
            """
        ).fetchall()

    return render_template("loans.html", loans=loan_list)


@app.route("/loans/add", methods=["GET", "POST"])
def add_loan():
    if request.method == "POST":
        borrower_name = request.form.get("borrower_name", "").strip()
        book_id_value = request.form.get("book_id", "")

        if not borrower_name:
            flash("Please enter a borrower name.", "error")
            return redirect(url_for("add_loan"))

        try:
            book_id = int(book_id_value)
            if not 1 <= book_id <= 2_147_483_647:
                raise ValueError
        except ValueError:
            flash("Please select a valid book.", "error")
            return redirect(url_for("add_loan"))

        try:
            with get_database_connection() as connection:
                loan = connection.execute(
                    """
                    INSERT INTO public.loans (book_id, borrower_name)
                    SELECT books.id, %s
                    FROM public.books AS books
                    WHERE books.id = %s
                      AND NOT EXISTS (
                          SELECT 1
                          FROM public.loans AS active_loan
                          WHERE active_loan.book_id = books.id
                            AND active_loan.returned_on IS NULL
                      )
                    RETURNING id
                    """,
                    (borrower_name, book_id),
                ).fetchone()
        except UniqueViolation:
            flash("That book has already been loaned out.", "error")
            return redirect(url_for("add_loan"))

        if loan is None:
            flash("That book is unavailable or no longer exists.", "error")
            return redirect(url_for("add_loan"))

        flash("Loan recorded.", "success")
        return redirect(url_for("loans"))

    with get_database_connection() as connection:
        available_books = connection.execute(
            """
            SELECT books.id, books.title, books.author, genres.name
            FROM public.books AS books
            JOIN public.genres AS genres ON genres.id = books.genre_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM public.loans AS active_loan
                WHERE active_loan.book_id = books.id
                  AND active_loan.returned_on IS NULL
            )
            ORDER BY books.title, books.author
            """
        ).fetchall()

    return render_template("add_loan.html", books=available_books)


@app.post("/loans/<int:loan_id>/return")
def return_loan(loan_id):
    with get_database_connection() as connection:
        returned_loan = connection.execute(
            """
            UPDATE public.loans
            SET returned_on = CURRENT_DATE
            WHERE id = %s AND returned_on IS NULL
            RETURNING id
            """,
            (loan_id,),
        ).fetchone()

    if returned_loan is None:
        flash("That loan is already returned or does not exist.", "error")
    else:
        flash("Book returned.", "success")

    return redirect(url_for("loans"))


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
    try:
        with get_database_connection() as connection:
            deleted_book = connection.execute(
                "DELETE FROM public.books WHERE id = %s RETURNING title",
                (book_id,),
            ).fetchone()
    except ForeignKeyViolation:
        flash("This book has loan history and cannot be removed.", "error")
        return redirect(url_for("books"))

    if deleted_book is None:
        flash("That book was not found.", "error")
    else:
        flash(f"Removed {deleted_book[0]}.", "success")

    return redirect(url_for("books"))


if __name__ == "__main__":
    app.run(debug=False)
