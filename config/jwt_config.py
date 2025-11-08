from flask import jsonify
from flask_jwt_extended import JWTManager
from models.user import User

jwt = JWTManager()

@jwt.user_identity_loader
def user_identity_lookup(user):
    return str(user.id)         # JWT exige string no campo 'sub'

@jwt.user_lookup_loader
def user_lookup_callback(_jwt_header, jwt_data):
    identity = jwt_data["sub"]
    return User.query.filter_by(id=int(identity)).one_or_none()     # converte de volta pra int quando buscar no banco


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_data):
    return jsonify({
        "message": "Token expirado",
        "error": "token_expired"
    }), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        "message": "Token inválido",
        "error": "invalid_token"
    }), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        "message": "Token ausente ou inválido",
        "error": "authorization_required"
    }), 401
