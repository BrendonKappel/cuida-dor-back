from flask import Blueprint, request, jsonify
from models.user import User
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Credenciais inválidas"}), 400

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Email ou senha incorretos"}), 401

    token = create_access_token(identity=user)

    return jsonify({
        "message": "Login realizado com sucesso",
        "token": token,
        "user": user.to_dict()
    }), 200
