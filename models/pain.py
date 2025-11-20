from models.user import db
import enum
from datetime import datetime

class PainType(enum.Enum):
    BEFORE_RELIEF_TECHNIQUES = "Antes"
    AFTER_RELIEF_TECHNIQUES = "Pós"

class Pain(db.Model):
    __tablename__ = "tb_pain"

    id = db.Column(db.Integer, primary_key=True)
    painLocale = db.Column(db.String(100), nullable=False)
    painScale = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum(PainType), nullable=False)
    dateTimeEvent = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("tb_user.id"), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "painLocale": self.painLocale,
            "painScale": self.painScale,
            "type": self.type.value,
            "dateTimeEvent": self.dateTimeEvent.strftime("%Y-%m-%d"),
        }
