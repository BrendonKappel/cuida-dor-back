import matplotlib
matplotlib.use("Agg")               # Não deixa o Matplotlib de abrir GUI (não quebra o código em execução)

import base64
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, current_user
from models.pain import Pain, PainType
from models.user import db

pain_bp = Blueprint("pain_bp", "pain_bp")

@pain_bp.route("/pain", methods=["POST"])
@jwt_required()
def create_pain():
    data = request.get_json()

    required = ["painLocale", "painScale", "type", "dateTimeEvent"]
    if not all(k in data for k in required):
        return jsonify({"error": "Dados incompletos"}), 400

    try:
        pain_type = PainType[data["type"]]
    except KeyError:
        return jsonify({"error": "Tipo de dor inválido"}), 400

    pain = Pain(
        painLocale=data["painLocale"],
        painScale=int(data["painScale"]),
        type=pain_type,
        dateTimeEvent=datetime.strptime(data["dateTimeEvent"], "%Y-%m-%d"),
        user_id=current_user.id
    )

    db.session.add(pain)
    db.session.commit()

    return jsonify({"message": "Evento de dor registrado com sucesso"}), 201


@pain_bp.route("/pain", methods=["GET"])
@jwt_required()
def get_pain_graph():
    size = request.args.get("size", type=int)
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    base_query = Pain.query.filter_by(user_id=current_user.id)

    if start_date:
        base_query = base_query.filter(
            Pain.dateTimeEvent >= datetime.strptime(start_date, "%Y-%m-%d")
        )
    if end_date:
        base_query = base_query.filter(
            Pain.dateTimeEvent <= datetime.strptime(end_date, "%Y-%m-%d")
        )

    if size:
        distinct_days = (
            db.session.query(Pain.dateTimeEvent)
            .filter(Pain.user_id == current_user.id)
            .group_by(Pain.dateTimeEvent)
            .order_by(Pain.dateTimeEvent.desc())
            .limit(size)
            .all()
        )

        if not distinct_days:
            return jsonify({"error": "Nenhum evento encontrado"}), 404

        selected_days = [d[0].date() for d in distinct_days]

        pains = (
            base_query
            .filter(db.func.date(Pain.dateTimeEvent).in_(selected_days))
            .order_by(Pain.dateTimeEvent.asc())
            .all()
        )

    else:
        pains = base_query.order_by(Pain.dateTimeEvent.asc()).all()

    if not pains:
        return jsonify({"error": "Nenhum evento encontrado"}), 404

    before_dates = []
    before_vals = []

    after_dates = []
    after_vals = []

    for p in pains:
        date_str = p.dateTimeEvent.strftime("%d/%m/%Y")

        if p.type == PainType.BEFORE_RELIEF_TECHNIQUES:
            before_dates.append(date_str)
            before_vals.append(p.painScale)
        else:
            after_dates.append(date_str)
            after_vals.append(p.painScale)

    # Parte de geração do gráfico
    plt.figure(figsize=(10, 4))

    plt.plot(before_dates, before_vals, "-o", color="red", label="Antes")
    plt.plot(after_dates, after_vals, "-o", color="green", label="Pós")

    plt.title("Intensidade da Dor por Dia")
    plt.xlabel("Data")
    plt.ylabel("Intensidade da Dor (0-10)")
    plt.ylim(0, 10)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)

    # Converter gráfico para base64
    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    plt.close()

    return jsonify({"image": img_base64}), 200
