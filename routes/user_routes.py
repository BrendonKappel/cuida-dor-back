from flask import Blueprint, request, jsonify
from models.user import db, User
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

user_bp = Blueprint("user_bp", __name__)

@user_bp.route("/user/register", methods=["POST"])
def register_user():
    data = request.get_json()
    if not data or "email" not in data or "password" not in data:
        return jsonify({"error": "Dados incompletos"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email já cadastrado"}), 400

    user = User(
        name=data.get("name"),
        email=data["email"],
        sex=data.get("sex", "nao_identificar"),
        comorbidades=data.get("comorbidades")
    )
    user.set_password(data["password"])


    db.session.add(user)
    db.session.commit()

    
    token = create_access_token(identity=user)

    return jsonify({"message": "Usuário criado com sucesso", "token": token}), 201


@user_bp.route("/user", methods=["GET"])
@jwt_required()                                 # Isso aqui informa que a rota precisa de autenticação via token
def list_users():
    users = User.query.all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.route("/user/<int:id>", methods=["GET"])
@jwt_required()
def get_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(user.to_dict()), 200

# OBS: To permitindo modificar senha/email, mas validar isso mais tarde
@user_bp.route("/user/<int:id>", methods=["PATCH"])
@jwt_required()
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    data = request.get_json()
    user.name = data.get("name", user.name)
    user.sex = data.get("sex", user.sex)
    user.comorbidades = data.get("comorbidades", user.comorbidades)
    user.email = data.get("email", user.email)

    if "password" in data:
        user.set_password(data["password"])

    db.session.commit()
    return jsonify({"message": "Usuário atualizado"}), 200


@user_bp.route("/user/profile", methods=["GET"])
@jwt_required()
def get_user_profile():
    current_user = get_jwt_identity()
    user = User.query.get(current_user)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(user.to_dict()), 200

@user_bp.route("/user/<int:id>", methods=["DELETE"])
@jwt_required()
def delete_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "Usuário deletado"}), 200
