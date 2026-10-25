CREATE TABLE IF NOT EXISTS public.genres (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS public.books (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre_id INTEGER NOT NULL REFERENCES public.genres (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS public.loans (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES public.books (id) ON DELETE RESTRICT,
    borrower_name TEXT NOT NULL,
    loaned_on DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL DEFAULT (CURRENT_DATE + 14),
    returned_on DATE,
    CHECK (returned_on IS NULL OR returned_on >= loaned_on)
);

CREATE UNIQUE INDEX IF NOT EXISTS loans_one_active_loan_per_book
    ON public.loans (book_id)
    WHERE returned_on IS NULL;
