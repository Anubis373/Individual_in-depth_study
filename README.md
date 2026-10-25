# Library database

The database uses PostgreSQL and starts with a `genres` table. Each genre has
an automatically generated unique ID and a required, unique name.

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

Open <http://127.0.0.1:5000> to add a genre and see the saved genres.
