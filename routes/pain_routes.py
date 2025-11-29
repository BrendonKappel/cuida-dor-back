import matplotlib
matplotlib.use("Agg")

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

    pains = base_query.order_by(Pain.dateTimeEvent.asc()).all()

    if not pains:
        return jsonify({"error": "Nenhum evento encontrado"}), 404

    from collections import defaultdict
    before_data = defaultdict(list)
    after_data = defaultdict(list)

    for p in pains:
        date_obj = p.dateTimeEvent.date()

        if p.type == PainType.BEFORE_RELIEF_TECHNIQUES:
            jittered_value = min(p.painScale + 0.15, 10)     # Caso pontos coincidirem descola 0,15
            before_data[date_obj].append(jittered_value)
        else:
            jittered_value = max(p.painScale - 0.15, 0)
            after_data[date_obj].append(jittered_value)

    all_dates = sorted(set(before_data.keys()) | set(after_data.keys()))

    dates_str = []
    before_vals = []
    after_vals = []

    for date_obj in all_dates:
        dates_str.append(date_obj.strftime("%d/%m/%Y"))

        before_vals.append(
            sum(before_data[date_obj]) / len(before_data[date_obj])
            if date_obj in before_data else None
        )
        after_vals.append(
            sum(after_data[date_obj]) / len(after_data[date_obj])
            if date_obj in after_data else None
        )

    all_before_values = [v for v in before_vals if v is not None]
    all_after_values = [v for v in after_vals if v is not None]

    mean_before = sum(all_before_values) / len(all_before_values) if all_before_values else None
    mean_after = sum(all_after_values) / len(all_after_values) if all_after_values else None

    plt.figure(figsize=(10, 4))
    plt.plot(dates_str, before_vals, "-o", color="red", label="Antes")
    plt.plot(dates_str, after_vals, "-o", color="green", label="Pós")

    plt.title("Intensidade da Dor por Dia (Média)")
    plt.xlabel("Data")
    plt.ylabel("Intensidade da Dor (0-10)")
    plt.ylim(0, 10.5)
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", dpi=100)
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    plt.close()

    return jsonify({
        "image": img_base64,
        "meanBefore": mean_before,
        "meanAfter": mean_after
    }), 200
