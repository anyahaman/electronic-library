from app import app
from extensions import db

from models import Role, User

from werkzeug.security import generate_password_hash



with app.app_context():

    # очищаем старые данные
    User.query.delete()
    Role.query.delete()

    db.session.commit()


    # создаём роли

    admin_role = Role(
        name="Администратор",
        description="Полный доступ к системе"
    )


    moderator_role = Role(
        name="Модератор",
        description="Редактирование книг и модерация отзывов"
    )


    user_role = Role(
        name="Пользователь",
        description="Может оставлять отзывы и создавать подборки"
    )


    db.session.add_all([
        admin_role,
        moderator_role,
        user_role
    ])


    db.session.commit()



    # создаём пользователей


    admin = User(
        login="admin",
        password_hash=generate_password_hash("admin123"),
        surname="Админов",
        name="Администратор",
        patronymic="Админович",
        role_id=admin_role.id
    )


    moderator = User(
        login="moderator",
        password_hash=generate_password_hash("moderator123"),
        surname="Модераторов",
        name="Модератор",
        patronymic="Модераторович",
        role_id=moderator_role.id
    )


    user = User(
        login="user",
        password_hash=generate_password_hash("user123"),
        surname="Пользователь",
        name="Иван",
        patronymic="Иванович",
        role_id=user_role.id
    )


    db.session.add_all([
        admin,
        moderator,
        user
    ])


    db.session.commit()


    print("Начальные данные добавлены!")