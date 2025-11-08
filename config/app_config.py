import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "Caio_Gostoso")   # SECRET_KEY é a variavel ambiente, se não tiver pega o Caio_Gostoso (lá ele)
    SQLALCHEMY_DATABASE_URI = "sqlite:///database.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = False  # Seta p/ token não expirar
