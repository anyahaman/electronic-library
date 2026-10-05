import os


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "dev-secret-key"
)

database_url = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root12345@localhost/electronic_library"
)

if database_url.startswith("mysql://"):
    database_url = database_url.replace(
        "mysql://",
        "mysql+pymysql://",
        1
    )

SQLALCHEMY_DATABASE_URI = database_url
SQLALCHEMY_TRACK_MODIFICATIONS = False