import typing as T
import random
import sqlite3

try:
    from graphql_example.factories import book_factory, author_factory
    from graphql_example.logging_utilities import *
except ModuleNotFoundError:
    from factories import book_factory, author_factory
    from logging_utilities import *

from eliot import to_file, use_asyncio_context


async def configure_logging(app):
    print('configuring logging')
    use_asyncio_context()

    logfile = app['config'].get('logfile', 'log.json')
    to_file(open(logfile, 'w'))


async def configure_database(app):
    with log_action('configuring database'):
        db = app['config'].get('db') or ':memory:'
        connection = sqlite3.connect(
            db,
            # here be dragons
            check_same_thread=False)
        # moar dragons
        connection.execute('PRAGMA synchronous = OFF')

        app['connection'] = connection

        log_message('connection established', db=db)


async def create_tables(app):
    with log_action('creating tables'):

        CREATE_TABLES = """
    
        CREATE TABLE IF NOT EXISTS author(
            id         INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            first_name TEXT NOT NULL,
            last_name  TEXT NOT NULL,
            age        INTEGER NOT NULL
        );
    
        CREATE TABLE IF NOT EXISTS book(
            id        INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
            title     TEXT NOT NULL,
            published TEXT NOT NULL,
            author_id INTEGER NOT NULL REFERENCES author(id)
    
        );
        """

        app['connection'].executescript(CREATE_TABLES)


async def seed_db(app):
    with log_action('seeding database'):

        connection = app['connection']

        authors: T.Tuple[T.Tuple] = tuple(
            (a.first_name, a.last_name, a.age)
            for a in (author_factory() for _ in range(200)))

        with connection:
            # insert 200 authors
            connection.executemany(
                'INSERT INTO author (first_name, last_name, age) VALUES (?, ?, ?)',
                authors)

            # insert 500 books
            author_ids = tuple(
                id for id, *_ in connection.execute('SELECT id FROM author'))

            books = []

            for _ in range(500):
                book = book_factory()
                author_id = random.choice(author_ids)
                books.append((book.title, book.published, author_id))

            connection.executemany(
                'INSERT INTO book (title, published, author_id) VALUES (?, ?, ?)',
                books)
