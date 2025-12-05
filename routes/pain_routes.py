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
    size = request.args.get("size", type=int)

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

    if size:
        pains = pains[:size]

    if not pains:
        return jsonify({"error": "Nenhum evento encontrado"}), 404

    from collections import defaultdict
    before_data = defaultdict(list)
    after_data = defaultdict(list)

    for p in pains:
        date_only = p.dateTimeEvent.date()

        if p.type == PainType.BEFORE_RELIEF_TECHNIQUES:
            before_data[date_only].append(p.painScale)
        else:
            after_data[date_only].append(p.painScale)

    all_dates = sorted(set(before_data.keys()) | set(after_data.keys()))

    dates_str = []
    before_vals = []
    after_vals = []

    for d in all_dates:
        dates_str.append(d.strftime("%d/%m/%Y"))
        before_vals.append(
            sum(before_data[d]) / len(before_data[d]) if d in before_data else None
        )
        after_vals.append(
            sum(after_data[d]) / len(after_data[d]) if d in after_data else None
        )

    all_before = [v for v in before_vals if v is not None]
    all_after = [v for v in after_vals if v is not None]

    mean_before = sum(all_before)/len(all_before) if all_before else None
    mean_after = sum(all_after)/len(all_after) if all_after else None

    plt.figure(figsize=(10, 3.3))

    plt.plot(dates_str, before_vals, "-o", color="red", label="Antes", markersize=6)
    plt.plot(dates_str, after_vals, "-o", color="green", label="Pós", markersize=6)

    plt.yticks([])
    plt.gca().spines["left"].set_visible(False)

    plt.xticks(rotation=45, fontsize=8)

    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.spines["bottom"].set_alpha(0.3)

    # Legenda
    plt.legend(fontsize=10, loc="upper left")

    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=110, bbox_inches="tight")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    plt.close()

    return jsonify({
        "image": img_base64,
        "meanBefore": mean_before,
        "meanAfter": mean_after
    }), 200




