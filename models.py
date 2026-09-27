from extensions import db
from flask_login import UserMixin
from datetime import datetime



# =========================
# КНИГИ - ЖАНРЫ
# =========================

books_genres = db.Table(
    "books_genres",

    db.Column(
        "book_id",
        db.Integer,
        db.ForeignKey(
            "books.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    ),

    db.Column(
        "genre_id",
        db.Integer,
        db.ForeignKey(
            "genres.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
)



# =========================
# КНИГИ - ПОДБОРКИ
# =========================

collections_books = db.Table(
    "collections_books",

    db.Column(
        "collection_id",
        db.Integer,
        db.ForeignKey(
            "collections.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    ),

    db.Column(
        "book_id",
        db.Integer,
        db.ForeignKey(
            "books.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )
)




# =========================
# РОЛИ
# =========================

class Role(db.Model):

    __tablename__ = "roles"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


    description = db.Column(
        db.Text,
        nullable=False
    )




# =========================
# ПОЛЬЗОВАТЕЛИ
# =========================

class User(db.Model, UserMixin):

    __tablename__ = "users"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    login = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


    password_hash = db.Column(
        db.String(255),
        nullable=False
    )


    surname = db.Column(
        db.String(100),
        nullable=False
    )


    name = db.Column(
        db.String(100),
        nullable=False
    )


    patronymic = db.Column(
        db.String(100)
    )


    role_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "roles.id"
        ),
        nullable=False
    )


    role = db.relationship(
        "Role"
    )


    collections = db.relationship(
        "Collection",
        back_populates="user",
        cascade="all, delete"
    )


    reviews = db.relationship(
        "Review",
        back_populates="user",
        cascade="all, delete"
    )




# =========================
# КНИГИ
# =========================

class Book(db.Model):

    __tablename__ = "books"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    title = db.Column(
        db.String(255),
        nullable=False
    )


    description = db.Column(
        db.Text,
        nullable=False
    )


    year = db.Column(
        db.Integer,
        nullable=False
    )


    publisher = db.Column(
        db.String(255),
        nullable=False
    )


    author = db.Column(
        db.String(255),
        nullable=False
    )


    pages = db.Column(
        db.Integer,
        nullable=False
    )



    genres = db.relationship(
        "Genre",
        secondary=books_genres,
        back_populates="books"
    )



    collections = db.relationship(
        "Collection",
        secondary=collections_books,
        back_populates="books"
    )



    cover = db.relationship(
        "Cover",
        back_populates="book",
        uselist=False,
        cascade="all, delete"
    )



    reviews = db.relationship(
        "Review",
        back_populates="book",
        cascade="all, delete"
    )




# =========================
# ЖАНРЫ
# =========================

class Genre(db.Model):

    __tablename__ = "genres"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )


    books = db.relationship(
        "Book",
        secondary=books_genres,
        back_populates="genres"
    )




# =========================
# ПОДБОРКИ
# =========================

class Collection(db.Model):

    __tablename__ = "collections"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    name = db.Column(
        db.String(255),
        nullable=False
    )


    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    user = db.relationship(
        "User",
        back_populates="collections"
    )



    books = db.relationship(
        "Book",
        secondary=collections_books,
        back_populates="collections"
    )




# =========================
# ОБЛОЖКИ
# =========================

class Cover(db.Model):

    __tablename__ = "covers"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    filename = db.Column(
        db.String(255),
        nullable=False
    )


    mime_type = db.Column(
        db.String(100),
        nullable=False
    )


    md5_hash = db.Column(
        db.String(255),
        nullable=False
    )


    book_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "books.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    book = db.relationship(
        "Book",
        back_populates="cover"
    )




# =========================
# РЕЦЕНЗИИ
# =========================

class Review(db.Model):

    __tablename__ = "reviews"


    id = db.Column(
        db.Integer,
        primary_key=True
    )


    book_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "books.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )


    rating = db.Column(
        db.Integer,
        nullable=False
    )


    text = db.Column(
        db.Text,
        nullable=False
    )


    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    book = db.relationship(
        "Book",
        back_populates="reviews"
    )


    user = db.relationship(
        "User",
        back_populates="reviews"
    )