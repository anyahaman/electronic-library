import os


class Config:

    SECRET_KEY = "super-secret-key"

    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:root12345@localhost/electronic_library"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "static/uploads"