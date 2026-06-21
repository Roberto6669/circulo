"""
CÍRCULO · Modelos de base de datos
-----------------------------------
Esquema relacional con el sistema de referidos / equipos (estilo Primerica).

El árbol de patrocinio vive en Member.sponsor_id:
  - sponsor_id  -> el miembro que te reclutó (tu upline). NULL si no tienes patrocinador.
  - recruits    -> tus referidos directos (backref). El downline completo se
                   obtiene recorriendo el árbol (ver helpers en app.py).
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Member(db.Model):
    __tablename__ = "members"
    id            = db.Column(db.Integer, primary_key=True)
    member_number = db.Column(db.String(20), unique=True, index=True)   # EC-2026-0001
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(160), unique=True, nullable=False, index=True)  # usuario
    phone         = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)            # nunca texto plano
    tier          = db.Column(db.String(20), default="MIEMBRO")          # FUNDADOR / MIEMBRO
    referral_code = db.Column(db.String(20), unique=True, index=True)    # lo que comparte
    points        = db.Column(db.Integer, default=0)                     # para premios futuros
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # --- Árbol de patrocinio (auto-referencia) ---
    sponsor_id = db.Column(db.Integer, db.ForeignKey("members.id"), nullable=True, index=True)
    recruits   = db.relationship(
        "Member",
        backref=db.backref("sponsor", remote_side=[id]),
        lazy="select",
    )

    def to_dict(self, extra=None):
        d = dict(
            id=self.id, member_number=self.member_number, name=self.name,
            email=self.email, phone=self.phone, tier=self.tier,
            referral_code=self.referral_code, points=self.points,
            sponsor_id=self.sponsor_id,
            created_at=self.created_at.isoformat() if self.created_at else None,
        )
        if extra:
            d.update(extra)
        return d


class Business(db.Model):
    __tablename__ = "businesses"
    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(160), nullable=False)
    category      = db.Column(db.String(60))
    email         = db.Column(db.String(160), unique=True, nullable=False, index=True)
    phone         = db.Column(db.String(40))
    password_hash = db.Column(db.String(255), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    offers = db.relationship("Offer", backref="business", lazy="select",
                             cascade="all, delete-orphan")

    def to_dict(self, extra=None):
        d = dict(id=self.id, name=self.name, category=self.category,
                 email=self.email, phone=self.phone,
                 created_at=self.created_at.isoformat() if self.created_at else None)
        if extra:
            d.update(extra)
        return d


class Offer(db.Model):
    __tablename__ = "offers"
    id          = db.Column(db.Integer, primary_key=True)
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False, index=True)
    category    = db.Column(db.String(60))
    title       = db.Column(db.String(200), nullable=False)
    terms       = db.Column(db.Text)
    image       = db.Column(db.Text)              # data URI o URL
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return dict(
            id=self.id, business_id=self.business_id,
            business=self.business.name if self.business else None,
            category=self.category, title=self.title, terms=self.terms,
            image=self.image,
            created_at=self.created_at.isoformat() if self.created_at else None,
        )


class Coupon(db.Model):
    __tablename__ = "coupons"
    id         = db.Column(db.Integer, primary_key=True)
    code       = db.Column(db.String(30), unique=True, nullable=False, index=True)
    kind       = db.Column(db.String(20), default="member")   # member / business
    active     = db.Column(db.Boolean, default=True)
    note       = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    uses = db.relationship("CouponUse", backref="coupon", lazy="select",
                           cascade="all, delete-orphan")

    def to_dict(self):
        return dict(
            id=self.id, code=self.code, kind=self.kind, active=self.active,
            note=self.note, uses=len(self.uses),
            used_by=[u.to_dict() for u in self.uses],
            created_at=self.created_at.isoformat() if self.created_at else None,
        )


class CouponUse(db.Model):
    __tablename__ = "coupon_uses"
    id         = db.Column(db.Integer, primary_key=True)
    coupon_id  = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=False)
    name       = db.Column(db.String(120))
    email      = db.Column(db.String(160))
    role       = db.Column(db.String(20))
    used_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return dict(name=self.name, email=self.email, role=self.role,
                    used_at=self.used_at.isoformat() if self.used_at else None)


class Contact(db.Model):
    __tablename__ = "contacts"
    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(120))
    email      = db.Column(db.String(160))
    message    = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return dict(name=self.name, email=self.email, message=self.message,
                    created_at=self.created_at.isoformat() if self.created_at else None)
