# Library database

The PostgreSQL database contains genres, books, and loans. Each book has a
title, author, and required genre. A loan records the borrower's name, loan
date, due date, and return date.

Create the database and apply the schema with PostgreSQL's command-line tools:

```sh
createdb library_db
psql -d library_db -f schema.sql
```

## Run the app

Install the Python dependencies and start the app from the project directory:

```sh
python -m pip install -r requirements.txt
python app.py
```

The app reads the PostgreSQL password from `pg_password` in `.env`. It connects
to `library_db` as `postgres` on `localhost` by default. To use different
connection settings, set `PGHOST`, `PGPORT`, `PGDATABASE`, or `PGUSER` in the
environment.

Open <http://127.0.0.1:5000> or <http://127.0.0.1:5000/loans> to view loan
history and mark books returned. Open <http://127.0.0.1:5000/loans/add> to
loan an available book; each loan is due 14 days after checkout. Open
<http://127.0.0.1:5000/books> to search, view, or remove books. Search titles
and authors by partial text, and filter by genre. Open
<http://127.0.0.1:5000/books/add> to add a book. Open
<http://127.0.0.1:5000/genre> to view or remove genres, or
<http://127.0.0.1:5000/genre/add> to add a genre.
