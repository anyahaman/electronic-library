import hashlib
import os
from pathlib import Path

import bleach
import markdown
from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import func
from werkzeug.utils import secure_filename

from app import app, db
from decorators import admin_required, editor_required
from models import (
    Book, Collection, Cover, Genre, Review,
    books_genres, collections_books,
)


ALLOWED_MARKDOWN_TAGS = [
    "p", "br", "strong", "em", "ul", "ol", "li", "blockquote",
    "code", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "a"
]
ALLOWED_MARKDOWN_ATTRIBUTES = {"a": ["href", "title"]}


def sanitize_markdown_source(value):
    """Экранирует HTML в исходном Markdown перед сохранением в БД."""
    return bleach.clean(value or "", tags=[], attributes={}, strip=False)


def render_markdown(value):
    """Преобразует сохранённый Markdown в безопасный HTML для шаблонов."""
    html = markdown.markdown(value or "", extensions=["extra", "sane_lists"])
    return bleach.clean(
        html,
        tags=ALLOWED_MARKDOWN_TAGS,
        attributes=ALLOWED_MARKDOWN_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


app.jinja_env.filters["markdown"] = render_markdown


def _upload_dir():
    folder = Path(app.root_path) / app.config.get("UPLOAD_FOLDER", "static/uploads")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_cover(book, uploaded_file):
    """Создаёт запись Cover и сохраняет файл, не дублируя одинаковые изображения."""
    if not uploaded_file or not uploaded_file.filename:
        raise ValueError("Обложка обязательна")

    data = uploaded_file.read()
    if not data:
        raise ValueError("Файл обложки пуст")

    md5_hash = hashlib.md5(data).hexdigest()
    original_name = secure_filename(uploaded_file.filename) or "cover"
    extension = os.path.splitext(original_name)[1].lower()

    existing_cover = Cover.query.filter_by(md5_hash=md5_hash).first()
    if existing_cover:
        storage_name = existing_cover.filename
    else:
        storage_name = f"{book.id}_{md5_hash}{extension}"
        (_upload_dir() / storage_name).write_bytes(data)

    cover = Cover(
        filename=storage_name,
        mime_type=uploaded_file.mimetype or "application/octet-stream",
        md5_hash=md5_hash,
        book_id=book.id,
    )
    db.session.add(cover)


# ==========================
# Главная страница
# ==========================

@app.route("/")
def index():
    page = request.args.get("page", 1, type=int)

    books = (
        db.session.query(
            Book,
            func.avg(Review.rating).label("avg_rating"),
            func.count(Review.id).label("review_count"),
        )
        .outerjoin(Review, Review.book_id == Book.id)
        .group_by(Book.id)
        .order_by(Book.year.desc())
        .paginate(page=page, per_page=10, error_out=False)
    )

    return render_template("index.html", books=books)


# ==========================
# Просмотр книги
# ==========================

@app.route("/book/<int:id>")
def book_page(id):
    book = Book.query.get_or_404(id)

    user_review = None
    user_collections = []

    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            book_id=id,
            user_id=current_user.id,
        ).first()

        if current_user.role and current_user.role.name == "Пользователь":
            user_collections = Collection.query.filter_by(
                user_id=current_user.id
            ).order_by(Collection.name).all()

    return render_template(
        "book.html",
        book=book,
        user_review=user_review,
        collections=user_collections,
    )


# ==========================
# Создание книги
# ==========================

@app.route("/book/create", methods=["GET", "POST"])
@admin_required
def create_book():
    genres = Genre.query.order_by(Genre.name).all()

    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            publisher = request.form.get("publisher", "").strip()
            author = request.form.get("author", "").strip()
            year = request.form.get("year", type=int)
            pages = request.form.get("pages", type=int)

            if not title or not description or not publisher or not author:
                raise ValueError("Не заполнены обязательные поля")
            if year is None or pages is None or pages <= 0:
                raise ValueError("Некорректный год или количество страниц")

            book = Book(
                title=title,
                description=sanitize_markdown_source(description),
                year=year,
                publisher=publisher,
                author=author,
                pages=pages,
            )

            for genre_id in request.form.getlist("genres"):
                genre = db.session.get(Genre, int(genre_id))
                if genre:
                    book.genres.append(genre)

            if not book.genres:
                raise ValueError("Необходимо выбрать хотя бы один жанр")

            db.session.add(book)
            db.session.flush()  # получаем book.id до commit

            save_cover(book, request.files.get("cover"))

            db.session.commit()
            flash("Книга успешно добавлена")
            return redirect(url_for("book_page", id=book.id))

        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. "
                "Проверьте корректность введённых данных."
            )

    return render_template(
        "create_book.html",
        genres=genres,
        form_data=request.form,
    )


# ==========================
# Редактирование книги
# ==========================

@app.route("/book/edit/<int:id>", methods=["GET", "POST"])
@editor_required
def edit_book(id):
    book = Book.query.get_or_404(id)
    genres = Genre.query.order_by(Genre.name).all()

    if request.method == "POST":
        try:
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            publisher = request.form.get("publisher", "").strip()
            author = request.form.get("author", "").strip()
            year = request.form.get("year", type=int)
            pages = request.form.get("pages", type=int)

            if not title or not description or not publisher or not author:
                raise ValueError("Не заполнены обязательные поля")
            if year is None or pages is None or pages <= 0:
                raise ValueError("Некорректный год или количество страниц")

            book.title = title
            book.description = sanitize_markdown_source(description)
            book.year = year
            book.publisher = publisher
            book.author = author
            book.pages = pages

            selected_genres = []
            for genre_id in request.form.getlist("genres"):
                genre = db.session.get(Genre, int(genre_id))
                if genre:
                    selected_genres.append(genre)

            if not selected_genres:
                raise ValueError("Необходимо выбрать хотя бы один жанр")

            book.genres = selected_genres
            db.session.commit()

            flash("Данные книги успешно обновлены")
            return redirect(url_for("book_page", id=book.id))

        except Exception:
            db.session.rollback()
            flash(
                "При сохранении данных возникла ошибка. "
                "Проверьте корректность введённых данных."
            )

    return render_template(
        "edit_book.html",
        book=book,
        genres=genres,
        form_data=request.form,
    )


# ==========================
# Удаление книги
# ==========================

@app.route("/book/delete/<int:id>", methods=["POST"])
@admin_required
def delete_book(id):
    book = Book.query.get_or_404(id)
    cover_filename = book.cover.filename if book.cover else None

    try:
        # Удаляем связи явно. Это важно, если база была создана раньше
        # и внешние ключи в ней ещё не имеют ON DELETE CASCADE.
        db.session.execute(
            books_genres.delete().where(books_genres.c.book_id == id)
        )
        db.session.execute(
            collections_books.delete().where(collections_books.c.book_id == id)
        )

        # Удаляем зависимые записи явно, чтобы удаление работало и на старой схеме БД.
        Review.query.filter_by(book_id=id).delete(synchronize_session=False)
        Cover.query.filter_by(book_id=id).delete(synchronize_session=False)

        db.session.delete(book)
        db.session.commit()

        # После успешного commit удаляем файл обложки с диска.
        if cover_filename:
            still_used = Cover.query.filter_by(filename=cover_filename).first()
            if not still_used:
                file_path = _upload_dir() / cover_filename
                if file_path.exists():
                    file_path.unlink()

        flash("Книга успешно удалена")

    except Exception as error:
        db.session.rollback()
        print(f"Ошибка при удалении книги {id}: {error}")
        flash("При удалении книги возникла ошибка")

    return redirect(url_for("index"))


# ==========================
# Создание рецензии
# ==========================

@app.route("/book/<int:id>/review/create", methods=["GET", "POST"])
@login_required
def create_review(id):
    book = Book.query.get_or_404(id)

    old_review = Review.query.filter_by(
        book_id=id,
        user_id=current_user.id,
    ).first()

    if old_review:
        flash("Вы уже оставляли рецензию на эту книгу")
        return redirect(url_for("book_page", id=id))

    if request.method == "POST":
        try:
            rating = int(request.form["rating"])
            text = request.form["text"].strip()

            if rating not in range(0, 6) or not text:
                raise ValueError("Некорректные данные")

            review = Review(
                book_id=id,
                user_id=current_user.id,
                rating=rating,
                text=sanitize_markdown_source(text),
            )

            db.session.add(review)
            db.session.commit()

            flash("Рецензия успешно добавлена")
            return redirect(url_for("book_page", id=id))

        except Exception:
            db.session.rollback()
            flash("При сохранении рецензии возникла ошибка")

    return render_template("create_review.html", book=book)


# ==========================
# Вариант 2: Подборки книг
# ==========================

def _require_regular_user():
    if not current_user.is_authenticated:
        flash("Для выполнения данного действия необходимо пройти процедуру аутентификации")
        return redirect(url_for("login"))
    if not current_user.role or current_user.role.name != "Пользователь":
        flash("У вас недостаточно прав для выполнения данного действия")
        return redirect(url_for("index"))
    return None


@app.route("/collections")
@login_required
def collections():
    denied = _require_regular_user()
    if denied:
        return denied

    user_collections = Collection.query.filter_by(
        user_id=current_user.id
    ).order_by(Collection.name).all()

    return render_template(
        "collections.html",
        collections=user_collections,
    )


@app.route("/collection/create", methods=["POST"])
@login_required
def create_collection():
    denied = _require_regular_user()
    if denied:
        return denied

    name = request.form.get("name", "").strip()
    if not name:
        flash("Введите название подборки")
        return redirect(url_for("collections"))

    collection = Collection(name=name, user_id=current_user.id)
    db.session.add(collection)
    db.session.commit()

    flash("Подборка успешно добавлена")
    return redirect(url_for("collections"))


@app.route("/collection/<int:id>")
@login_required
def collection_view(id):
    denied = _require_regular_user()
    if denied:
        return denied

    collection = Collection.query.filter_by(
        id=id,
        user_id=current_user.id,
    ).first_or_404()

    return render_template("collection_view.html", collection=collection)


@app.route("/collection/add/<int:book_id>", methods=["POST"])
@login_required
def add_book_to_collection(book_id):
    denied = _require_regular_user()
    if denied:
        return denied

    book = Book.query.get_or_404(book_id)
    collection_id = request.form.get("collection", type=int)

    collection = Collection.query.filter_by(
        id=collection_id,
        user_id=current_user.id,
    ).first()

    if not collection:
        flash("Выбранная подборка не найдена")
        return redirect(url_for("book_page", id=book_id))

    if book in collection.books:
        flash("Эта книга уже находится в выбранной подборке")
        return redirect(url_for("book_page", id=book_id))

    collection.books.append(book)
    db.session.commit()

    flash("Книга успешно добавлена в подборку")
    return redirect(url_for("book_page", id=book_id))
