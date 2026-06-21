# CÍRCULO · Backend (Fase 1)

Backend en Flask + PostgreSQL para el club CÍRCULO. Incluye autenticación segura
(contraseñas encriptadas), y el sistema de **referidos y equipos estilo Primerica**.

## Qué hace esta fase
- Registro y login de **miembros** y **negocios** (contraseñas con hash, nunca texto plano).
- **Código de referido** por miembro → al registrarse con él se arma el árbol de equipos.
- Endpoints de **referidos** y **mi equipo** (downline completo, tamaño, niveles).
- Ofertas, cupones, contacto y un **panel de admin** protegido con PIN.
- **Ranking de equipos** (`/api/admin/leaderboard`) — base para los premios futuros.

## Estructura
```
circulo-backend/
├── app.py            # API + sirve el frontend
├── models.py         # esquema de la base de datos
├── seed.py           # datos demo (incluye un árbol de referidos)
├── requirements.txt
├── Procfile          # arranque en Render (gunicorn)
└── static/
    └── index.html    # ← copia aquí tu frontend (el de v1.9)
```

## Correr en tu Mac (local)
```bash
cd circulo-backend
pip install -r requirements.txt --break-system-packages
python3 seed.py --reset          # crea las tablas + datos demo (SQLite)
python3 app.py                   # abre http://127.0.0.1:5000
```

**Cuentas demo** (después del seed):
- Cliente: `cliente@demo.com` / `demo123`  — ya tiene un equipo de 5 personas en 2 niveles
- Negocio: `hola@habana1958.com` / `demo123`

## Endpoints principales
| Método | Ruta | Para qué |
|---|---|---|
| POST | `/api/register/member` | Registrar miembro (acepta `referral_code`) |
| POST | `/api/register/business` | Registrar negocio |
| POST | `/api/login` | Login unificado (cliente o negocio) |
| GET | `/api/me` | Mi perfil (con token) |
| GET | `/api/referrals` | Mis referidos directos |
| GET | `/api/team` | Mi equipo completo + tamaño + niveles |
| GET | `/api/offers` | Catálogo de ofertas |
| POST | `/api/offers` | Publicar oferta (negocio) |
| POST | `/api/contact` | Enviar mensaje de contacto |
| GET | `/api/admin/stats` · `/members` · `/businesses` · `/leaderboard` | Admin (header `X-Admin-Pin`) |

El token de login se manda en el header `Authorization: Bearer <token>`.

## Desplegar en Render
1. Sube esta carpeta a un repo de GitHub.
2. En Render: **New → Web Service** (ya no Static Site), apuntando al repo.
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
3. **New → PostgreSQL** (crea la base de datos). Copia su *Internal Database URL*.
4. En el Web Service → **Environment**, agrega:
   - `DATABASE_URL` = la URL de Postgres del paso 3
   - `SECRET_KEY` = una clave larga al azar
   - `ADMIN_PIN` = tu PIN de administrador
5. Primer despliegue: las tablas se crean solas. Para los datos demo, abre el
   **Shell** del servicio en Render y corre: `python seed.py`

## Variables de entorno
| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | SQLite local | Conexión a PostgreSQL en producción |
| `SECRET_KEY` | (inseguro) | Firma los tokens — **cámbiala** en producción |
| `ADMIN_PIN` | `2026` | PIN del panel de administración |

## Siguiente fase
Conectar el frontend (`static/index.html`) a esta API: reemplazar el `localStorage`
por llamadas `fetch` a `/api/...`, y agregar la pantalla **"Mi equipo"** con el link
de referido. Después: puntos, premios y promociones por tamaño de equipo.
