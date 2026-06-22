"""
CÍRCULO · Backend (Flask)
=========================
Sirve el frontend (static/index.html) y expone una API REST con:
  - Autenticación con contraseñas encriptadas (Werkzeug) + token firmado.
  - Registro de miembros con CÓDIGO DE REFERIDO -> arma el árbol de equipos.
  - Endpoints de referidos y de "mi equipo" (downline completo + tamaño).
  - Negocios, ofertas, cupones, contacto y un panel de admin básico.

Base de datos: PostgreSQL en producción (DATABASE_URL) o SQLite en local.
"""
import os
from functools import wraps
from datetime import datetime

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from models import db, Member, Business, Offer, Coupon, CouponUse, Contact

# --------------------------------------------------------------------------- #
#  Configuración
# --------------------------------------------------------------------------- #
app = Flask(__name__, static_folder="static")
CORS(app)  # útil mientras el frontend y la API se prueban por separado

db_url = os.environ.get("DATABASE_URL", "sqlite:///circulo.db")
if db_url.startswith("postgres://"):                 # Render/Heroku usan postgres://
    db_url = db_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "cambia-esta-clave-en-produccion")

ADMIN_PIN  = os.environ.get("ADMIN_PIN", "2026")
MEMBER_FEE = 1.99
BUSINESS_FEE = 99
FOUNDER_LIMIT = 5000                                  # los primeros 5.000 son FUNDADOR

db.init_app(app)
with app.app_context():
    db.create_all()

# --------------------------------------------------------------------------- #
#  Tokens / autenticación
# --------------------------------------------------------------------------- #
def _serializer():
    return URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="circulo-auth")

def make_token(kind, uid):
    return _serializer().dumps({"kind": kind, "id": uid})

def read_token(token, max_age=60 * 60 * 24 * 30):     # 30 días
    try:
        return _serializer().loads(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None

def current_user():
    """Devuelve (kind, objeto) a partir del header Authorization: Bearer <token>."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        data = read_token(auth[7:])
        if data:
            if data["kind"] == "member":
                return "member", db.session.get(Member, data["id"])
            if data["kind"] == "business":
                return "business", db.session.get(Business, data["id"])
    return None, None

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        kind, user = current_user()
        if not user:
            return jsonify(error="No autenticado"), 401
        return f(kind, user, *args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        pin = request.headers.get("X-Admin-Pin", "")
        if pin != ADMIN_PIN:
            return jsonify(error="PIN de administrador incorrecto"), 401
        return f(*args, **kwargs)
    return wrapper

# --------------------------------------------------------------------------- #
#  Helpers de referidos / equipos
# --------------------------------------------------------------------------- #
def next_member_identifiers(member):
    """member_number y referral_code derivados del id (únicos y estables)."""
    member.member_number = f"EC-2026-{member.id:04d}"
    member.referral_code = member.member_number

def assign_tier():
    """Los primeros FOUNDER_LIMIT miembros son FUNDADOR; luego MIEMBRO."""
    founders = Member.query.filter_by(tier="FUNDADOR").count()
    return "FUNDADOR" if founders < FOUNDER_LIMIT else "MIEMBRO"

def find_sponsor(code):
    code = (code or "").strip().upper()
    if not code:
        return None
    return Member.query.filter(
        (Member.referral_code == code) | (Member.member_number == code)
    ).first()

def get_downline(member):
    """Recorre todo el árbol hacia abajo. Devuelve [(miembro, nivel), ...]."""
    out, queue = [], [(r, 1) for r in member.recruits]
    while queue:
        m, level = queue.pop(0)
        out.append((m, level))
        for r in m.recruits:
            queue.append((r, level + 1))
    return out

# --------------------------------------------------------------------------- #
#  Servir el frontend
# --------------------------------------------------------------------------- #
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/health")
def health():
    return jsonify(ok=True, time=datetime.utcnow().isoformat())

@app.get("/api/stats")
def public_stats():
    """Conteos públicos para el hero (sin datos sensibles)."""
    return jsonify(
        members=Member.query.count(),
        businesses=Business.query.count(),
        offers=Offer.query.count(),
    )

# --------------------------------------------------------------------------- #
#  AUTENTICACIÓN
# --------------------------------------------------------------------------- #
@app.post("/api/register/member")
def register_member():
    d = request.get_json(silent=True) or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip().lower()
    phone = (d.get("phone") or "").strip()
    pwd   = d.get("password") or ""
    ref   = d.get("referral_code")

    if not name or not email:
        return jsonify(error="Nombre y correo son obligatorios."), 400
    if len(pwd) < 4:
        return jsonify(error="La contraseña debe tener al menos 4 caracteres."), 400
    if Member.query.filter_by(email=email).first():
        return jsonify(error="Ese correo ya tiene una cuenta."), 409

    sponsor = None
    if ref:
        sponsor = find_sponsor(ref)
        if not sponsor:
            return jsonify(error="El código de referido no existe."), 400

    m = Member(
        name=name, email=email, phone=phone,
        password_hash=generate_password_hash(pwd),
        tier=assign_tier(),
        sponsor_id=sponsor.id if sponsor else None,
        points=0,
    )
    db.session.add(m)
    db.session.flush()                # obtener el id
    next_member_identifiers(m)
    db.session.commit()
    return jsonify(token=make_token("member", m.id), member=m.to_dict()), 201


@app.post("/api/register/business")
def register_business():
    d = request.get_json(silent=True) or {}
    name  = (d.get("name") or "").strip()
    cat   = (d.get("category") or "").strip()
    email = (d.get("email") or "").strip().lower()
    phone = (d.get("phone") or "").strip()
    pwd   = d.get("password") or ""

    if not name or not email:
        return jsonify(error="Nombre y correo del negocio son obligatorios."), 400
    if len(pwd) < 4:
        return jsonify(error="La contraseña debe tener al menos 4 caracteres."), 400
    if Business.query.filter_by(email=email).first():
        return jsonify(error="Ese correo ya tiene un negocio."), 409

    b = Business(name=name, category=cat, email=email, phone=phone,
                 password_hash=generate_password_hash(pwd))
    db.session.add(b)
    db.session.commit()
    return jsonify(token=make_token("business", b.id), business=b.to_dict()), 201


@app.post("/api/login")
def login():
    """Login unificado: busca el correo en miembros y en negocios."""
    d = request.get_json(silent=True) or {}
    email = (d.get("email") or "").strip().lower()
    pwd   = d.get("password") or ""

    m = Member.query.filter_by(email=email).first()
    if m and check_password_hash(m.password_hash, pwd):
        return jsonify(token=make_token("member", m.id), role="member", profile=m.to_dict())

    b = Business.query.filter_by(email=email).first()
    if b and check_password_hash(b.password_hash, pwd):
        return jsonify(token=make_token("business", b.id), role="business", profile=b.to_dict())

    return jsonify(error="Correo o contraseña incorrectos."), 401


@app.get("/api/me")
@login_required
def me(kind, user):
    return jsonify(role=kind, profile=user.to_dict())


@app.post("/api/me/update")
@login_required
def update_me(kind, user):
    """Actualiza nombre / teléfono / correo del usuario logueado."""
    d = request.get_json(silent=True) or {}
    name  = (d.get("name") or "").strip()
    phone = (d.get("phone") or "").strip()
    email = (d.get("email") or "").strip().lower()
    if name:
        user.name = name
    user.phone = phone
    if email and email != user.email:
        Model = Member if kind == "member" else Business
        if Model.query.filter(Model.email == email, Model.id != user.id).first():
            return jsonify(error="Ese correo ya está en uso."), 409
        user.email = email
    db.session.commit()
    return jsonify(role=kind, profile=user.to_dict())

# --------------------------------------------------------------------------- #
#  REFERIDOS / EQUIPOS
# --------------------------------------------------------------------------- #
@app.get("/api/referrals")
@login_required
def my_referrals(kind, user):
    """Récord de referidos directos del miembro."""
    if kind != "member":
        return jsonify(error="Solo para miembros."), 403
    recs = sorted(user.recruits, key=lambda x: x.created_at or datetime.min)
    return jsonify(
        referral_code=user.referral_code,
        count=len(recs),
        referrals=[{
            "name": r.name, "member_number": r.member_number, "email": r.email,
            "tier": r.tier,
            "joined": r.created_at.isoformat() if r.created_at else None,
        } for r in recs],
    )


@app.get("/api/team")
@login_required
def my_team(kind, user):
    """Equipo completo (downline en todos los niveles) + métricas."""
    if kind != "member":
        return jsonify(error="Solo para miembros."), 403
    downline = get_downline(user)
    by_level = {}
    for _, lvl in downline:
        by_level[lvl] = by_level.get(lvl, 0) + 1
    return jsonify(
        referral_code=user.referral_code,
        direct_count=len(user.recruits),                 # referidos directos
        team_size=len(downline),                         # equipo total (todos los niveles)
        depth=max([lvl for _, lvl in downline], default=0),
        by_level=by_level,
        direct=[r.to_dict() for r in user.recruits],
        team=[m.to_dict({"level": lvl}) for m, lvl in downline],
    )

# --------------------------------------------------------------------------- #
#  OFERTAS  (catálogo público + alta por el negocio)
# --------------------------------------------------------------------------- #
@app.get("/api/offers")
def list_offers():
    offers = Offer.query.order_by(Offer.created_at.desc()).all()
    return jsonify(offers=[o.to_dict() for o in offers])


@app.post("/api/offers")
@login_required
def create_offer(kind, user):
    if kind != "business":
        return jsonify(error="Solo los negocios pueden publicar ofertas."), 403
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    if not title:
        return jsonify(error="El título del descuento es obligatorio."), 400
    o = Offer(business_id=user.id, category=user.category, title=title,
              terms=(d.get("terms") or "Consulta términos en el local."),
              image=d.get("image"))
    db.session.add(o)
    db.session.commit()
    return jsonify(offer=o.to_dict()), 201


@app.put("/api/offers/<int:offer_id>")
@login_required
def update_offer(kind, user, offer_id):
    o = db.session.get(Offer, offer_id)
    if not o or (kind != "business") or o.business_id != user.id:
        return jsonify(error="No autorizado."), 403
    d = request.get_json(silent=True) or {}
    title = (d.get("title") or "").strip()
    if title:
        o.title = title
    if "terms" in d:
        o.terms = (d.get("terms") or "").strip() or "Consulta términos en el local."
    if d.get("image") is not None:
        o.image = d.get("image")
    db.session.commit()
    return jsonify(offer=o.to_dict())


@app.delete("/api/offers/<int:offer_id>")
@login_required
def delete_offer(kind, user, offer_id):
    o = db.session.get(Offer, offer_id)
    if not o or (kind != "business") or o.business_id != user.id:
        return jsonify(error="No autorizado."), 403
    db.session.delete(o)
    db.session.commit()
    return jsonify(ok=True)

# --------------------------------------------------------------------------- #
#  CUPONES  (validar + admin genera)
# --------------------------------------------------------------------------- #
@app.get("/api/coupons/<code>")
def check_coupon(code):
    c = Coupon.query.filter_by(code=code.strip().upper()).first()
    if not c:
        return jsonify(found=False), 404
    return jsonify(found=True, coupon=c.to_dict())


@app.get("/api/validate/<code>")
def validate_code(code):
    """Para los negocios: valida un número de miembro O un cupón.
    Acepta el QR completo 'CIRCULO|EC-2026-0001|...' o el código pelado."""
    raw = (code or "").strip().upper()
    num = raw
    if raw.startswith("CIRCULO|"):
        parts = raw.split("|")
        num = parts[1] if len(parts) > 1 else raw
    m = Member.query.filter(
        (Member.member_number == num) | (Member.referral_code == num)
    ).first()
    if m:
        return jsonify(type="member", valid=True, member={
            "name": m.name, "member_number": m.member_number,
            "tier": m.tier, "status": "Activa",
        })
    c = Coupon.query.filter_by(code=num).first()
    if c:
        return jsonify(type="coupon", valid=bool(c.active), coupon=c.to_dict())
    return jsonify(type="none", valid=False), 404

# --------------------------------------------------------------------------- #
#  CONTACTO
# --------------------------------------------------------------------------- #
@app.post("/api/contact")
def contact():
    d = request.get_json(silent=True) or {}
    c = Contact(name=(d.get("name") or "").strip(),
                email=(d.get("email") or "").strip(),
                message=(d.get("message") or "").strip())
    db.session.add(c)
    db.session.commit()
    return jsonify(ok=True), 201

# --------------------------------------------------------------------------- #
#  ADMIN  (protegido por X-Admin-Pin)
# --------------------------------------------------------------------------- #
@app.get("/api/admin/stats")
@admin_required
def admin_stats():
    return jsonify(
        members=Member.query.count(),
        businesses=Business.query.count(),
        offers=Offer.query.count(),
        coupon_uses=CouponUse.query.count(),
        contacts=Contact.query.count(),
    )


@app.get("/api/admin/members")
@admin_required
def admin_members():
    rows = Member.query.order_by(Member.id).all()
    return jsonify(members=[
        m.to_dict({"direct": len(m.recruits), "team_size": len(get_downline(m))})
        for m in rows
    ])


@app.get("/api/admin/businesses")
@admin_required
def admin_businesses():
    rows = Business.query.order_by(Business.id).all()
    return jsonify(businesses=[b.to_dict({"offers": len(b.offers)}) for b in rows])


@app.get("/api/admin/contacts")
@admin_required
def admin_contacts():
    rows = Contact.query.order_by(Contact.created_at.desc()).all()
    return jsonify(contacts=[c.to_dict() for c in rows])


@app.get("/api/admin/coupons")
@admin_required
def admin_list_coupons():
    rows = Coupon.query.order_by(Coupon.created_at.desc()).all()
    return jsonify(coupons=[c.to_dict() for c in rows])


@app.post("/api/admin/coupons/<code>/toggle")
@admin_required
def admin_toggle_coupon(code):
    c = Coupon.query.filter_by(code=code.strip().upper()).first()
    if not c:
        return jsonify(error="Cupón no encontrado."), 404
    c.active = not c.active
    db.session.commit()
    return jsonify(coupon=c.to_dict())


@app.post("/api/admin/coupons")
@admin_required
def admin_make_coupons():
    import random, string
    d = request.get_json(silent=True) or {}
    kind = d.get("kind", "member")
    qty = max(1, min(int(d.get("qty", 1)), 50))
    note = d.get("note", "")
    made = []
    for _ in range(qty):
        code = "EC-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4)) \
                     + "-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        db.session.add(Coupon(code=code, kind=kind, note=note, active=True))
        made.append(code)
    db.session.commit()
    return jsonify(codes=made), 201


# Ranking de equipos (útil para premios más adelante)
@app.get("/api/admin/leaderboard")
@admin_required
def admin_leaderboard():
    rows = Member.query.all()
    ranked = sorted(
        ({"name": m.name, "member_number": m.member_number,
          "direct": len(m.recruits), "team_size": len(get_downline(m))} for m in rows),
        key=lambda x: x["team_size"], reverse=True,
    )
    return jsonify(leaderboard=ranked[:50])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
