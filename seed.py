"""
Siembra datos demo en la base de datos.
Crea negocios, un cliente demo y un ARBOL DE REFERIDOS de ejemplo para
poder ver cómo funcionan los equipos.

Uso:
    python seed.py            # siembra si está vacío
    python seed.py --reset    # borra todo y vuelve a sembrar
"""
import sys
from werkzeug.security import generate_password_hash

from app import app, db, next_member_identifiers
from models import Member, Business, Offer, Coupon


def make_member(name, email, sponsor=None, tier="MIEMBRO", pwd="demo123"):
    m = Member(name=name, email=email, phone="(305) 555-0100",
               password_hash=generate_password_hash(pwd), tier=tier,
               sponsor_id=sponsor.id if sponsor else None)
    db.session.add(m)
    db.session.flush()
    next_member_identifiers(m)
    return m


def seed():
    # --- Negocios + una oferta cada uno ---
    negocios = [
        ("Café Habana 1958", "Restaurante", "hola@habana1958.com", "15% de descuento en el total"),
        ("Barbería El Clásico", "Belleza", "citas@elclasico.com", "Corte + barba por $25"),
        ("Taller AutoPro Miami", "Automotriz", "info@autopro.com", "Cambio de aceite a mitad de precio"),
        ("Dulce Caribe Bakery", "Restaurante", "pedidos@dulcecaribe.com", "Docena de pastelitos gratis en tu cumpleaños"),
        ("Glow Spa Brickell", "Belleza", "spa@glowbrickell.com", "20% en tu primer facial"),
    ]
    for nombre, cat, email, oferta in negocios:
        b = Business(name=nombre, category=cat, email=email, phone="(305) 555-0100",
                     password_hash=generate_password_hash("demo123"))
        db.session.add(b)
        db.session.flush()
        db.session.add(Offer(business_id=b.id, category=cat, title=oferta,
                             terms="No acumulable con otras promociones."))

    # --- Árbol de referidos de ejemplo ---
    #   Roberto (FUNDADOR)
    #   ├── María ── Pedro, Ana
    #   └── Juan  ── Luis
    roberto = make_member("Cliente Demo", "cliente@demo.com", tier="FUNDADOR")
    maria   = make_member("María Gómez", "maria@demo.com",  sponsor=roberto, tier="FUNDADOR")
    juan    = make_member("Juan Pérez",  "juan@demo.com",   sponsor=roberto, tier="FUNDADOR")
    make_member("Pedro Ruiz", "pedro@demo.com", sponsor=maria)
    make_member("Ana Torres", "ana@demo.com",   sponsor=maria)
    make_member("Luis Díaz",  "luis@demo.com",  sponsor=juan)

    # --- Cupón demo ---
    db.session.add(Coupon(code="EC-DEMO-2026", kind="member", note="Cupón de prueba"))

    db.session.commit()
    print("✓ Datos demo creados.")
    print("  Login cliente:  cliente@demo.com / demo123  (tiene un equipo de 5)")
    print("  Login negocio:  hola@habana1958.com / demo123")


if __name__ == "__main__":
    with app.app_context():
        if "--reset" in sys.argv:
            db.drop_all()
            db.create_all()
            print("✓ Base de datos reiniciada.")
        if Member.query.count() == 0 and Business.query.count() == 0:
            seed()
        else:
            print("La base de datos ya tiene datos. Usa --reset para empezar de cero.")
