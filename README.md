# Library database

The database uses PostgreSQL and starts with a `genres` table. Each genre has
an automatically generated unique ID and a required, unique name.

Create the database and apply the schema with PostgreSQL's command-line tools:

```sh
createdb library_db
psql -d library_db -f schema.sql
```
