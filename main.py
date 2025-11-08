from flask import Flask
from flask_cors import CORS
from config.app_config import Config
from models.user import db
from config.jwt_config import jwt
from routes.user_routes import user_bp
from routes.auth_routes import auth_bp

app = Flask(__name__)
app.config.from_object(Config)

CORS(app)
db.init_app(app)
jwt.init_app(app)

app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    return {"message": "API Flask rodando!"}

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
