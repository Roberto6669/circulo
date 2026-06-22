# CÍRCULO — Estado del proyecto (handoff para Claude)

**Última actualización:** 22 de junio de 2026
**Para:** cualquier Claude que continúe este proyecto, en cualquiera de las computadoras de Roberto
(Mac Mini M1, iMac M4, MacBook Air M2).
**Lee este archivo COMPLETO antes de trabajar.** Resume qué es el proyecto, dónde está parado y cómo seguir.

> **🆕 Cómo se trabaja AHORA (junio 2026):** Roberto dejó de usar Claude por Safari. De aquí en
> adelante el proyecto se lleva **dentro de Cowork (la app de escritorio de Claude)**, que es donde
> estás tú. Eso significa que **TÚ eres el protagonista**: tienes acceso directo a la carpeta del
> proyecto (puedes leer/editar archivos con las herramientas Read/Write/Edit) y a un **shell Linux
> aislado (sandbox)** para correr Python, probar el backend, hacer commits locales, etc. Ya no
> dependes de dictarle comandos a Roberto para todo — haz tú el trabajo y muéstrale el resultado.
> Lo único que sigue necesitando SU Mac es el **`git push` a GitHub** (las credenciales viven en su
> máquina, no en tu sandbox) y correr la app localmente si quiere verla en su navegador. Ver sección 13.

---

## ⚠️ Lo más importante primero (no lo olvides)

- **Roberto NO es experto en programación.** Es autodidacta. Explícale en términos simples y, cuando
  le toque hacer algo a él (ej. el push), dale **comandos exactos para copiar y pegar**, un paso a la
  vez. Confirma cada paso antes del siguiente.
- **Su terminal (zsh) NO acepta comentarios con `#`.** Si pones líneas con `#` dentro de un bloque de
  comandos, fallan con `command not found: #`. **Nunca pongas comentarios dentro de los bloques de shell.**
  Pon las explicaciones como texto aparte.
- **El proyecto vive en iCloud y eso TRABA git.** Ver sección 13 para los workarounds (HEAD.lock, etc.).
- **El sandbox no puede usar SQLite sobre la carpeta de iCloud** (da `disk I/O error`). Para probar el
  backend, copia los archivos a `/tmp` y corre ahí. Ver sección 13.
- En la Mac de Roberto, `pip` es **`pip3`**, y hay que usar **`--break-system-packages`**.
- Conversa en **español**.

---

## 1. Qué es CÍRCULO

Un **club privado de descuentos** para la comunidad latina de Miami. Los miembros pagan una membresía
única ($1.99 de por vida) y obtienen descuentos en negocios locales mostrando su carnet digital. Los
negocios pagan ($99/año o con cupón) para publicar ofertas.

Lo construye **Roberto Escobar Citty**, RVP de Primerica en Miami. Por eso el proyecto incluye un
**sistema de referidos y equipos estilo Primerica** (reclutas, downline, premios por tamaño de equipo).

## 2. Arquitectura

**Full-stack, un solo repo, un solo deploy:**
- **Backend:** Flask (`app.py`) + SQLAlchemy (`models.py`) + PostgreSQL.
- **Frontend:** un solo archivo `static/index.html` (HTML/CSS/JS vanilla, sin build).
- **Flask sirve las dos cosas:** el frontend en `/` y la API en `/api/...`. Por eso el frontend
  llamará a la API en la **misma URL** (sin CORS ni URLs quemadas).
- **Base de datos:** PostgreSQL en producción (vía `DATABASE_URL`), SQLite en local.
- **Despliegue:** Render (Web Service + Postgres), configurado con `render.yaml`.

## 3. ⭐ DÓNDE ESTAMOS PARADOS (estado actual)

- **Frontend:** versión **v2.0**, ✅ **conectado al API.** Ya NO usa `localStorage` para los datos:
  todo pasa por `fetch` a `/api/...`. El token de login se guarda en `localStorage` y se manda en el
  header `Authorization: Bearer`. Capa `API` + objeto `Session` (ver sección 11).
- **Backend (Fase 1 + extras de Fase 2):** ✅ **COMPLETO y probado.** Auth con contraseñas encriptadas
  (scrypt), miembros, negocios, ofertas, cupones, contacto, referidos/equipos. En la Fase 2 se agregaron:
  `/api/stats` (público), `/api/me/update`, `PUT /api/offers/<id>`, `/api/validate/<code>`,
  `GET /api/admin/coupons` y `POST /api/admin/coupons/<code>/toggle`. Verificado con 23 pruebas e2e (test client).
- **Despliegue:** el código completo está en GitHub (`Roberto6669/circulo`), se despliega en Render vía
  Blueprint. URL esperada: `https://circulo-backend.onrender.com`.
- **✅ Fase 2 LISTA — frontend y backend conectados.** Lo siguiente es la **Fase 3 (pantalla "Mi equipo")**.

> **Limitaciones conocidas (para retomar):** (1) el cupón en el registro se valida pero su "uso" NO se
> registra en el server (no hay endpoint de canje aún), así que el contador de usos en admin queda en 0.
> (2) El admin ya NO muestra contraseñas (el backend nunca las devuelve); ahora muestra Equipo/Teléfono.
> (3) Una misma cuenta ya no puede ser cliente Y negocio a la vez (el login devuelve un solo rol).
> (4) El botón "Resetear" del admin solo informa; para reiniciar datos se corre `seed.py` en el server.

## 4. Roadmap (fases)

1. **Fase 1 — Backend ✅ HECHO.** API + base de datos + auth + referidos/equipos.
2. **Fase 2 — Conectar el frontend a la API ✅ HECHO.** El `localStorage` de datos se reemplazó por
   `fetch` a `/api/...`; el token se guarda y se manda en cada llamada (capa `API` + `Session`).
3. **Fase 3 — Pantalla "Mi equipo" (← SIGUIENTE).** Link de referido para compartir, referidos directos, árbol del
   equipo, tamaño del equipo. (Backend ya listo: `/api/team`, `/api/referrals`.)
4. **Fase 4 — Premios y promociones.** Puntos, rankings (`/api/admin/leaderboard` ya existe),
   recompensas por tamaño de equipo.

## 5. ⭐ El modelo de referidos / equipos (estilo Primerica)

Es el corazón del proyecto. Vive en `Member.sponsor_id`:
- Cada miembro tiene un **código de referido** (`referral_code`, que es igual a su `member_number`,
  ej. `EC-2026-0001`).
- Cuando alguien se registra con ese código, su `sponsor_id` apunta al que lo refirió. Así se arma un
  **árbol** sin límite de niveles.
- **Referidos directos** = miembros cuyo `sponsor_id` eres tú (`member.recruits`).
- **Equipo / downline** = todo el árbol hacia abajo (todos los niveles). Se calcula recorriendo el
  árbol con `get_downline()` en `app.py`.
- **Fundadores:** los primeros 5.000 miembros tienen `tier = "FUNDADOR"` (beneficio que se cierra a los
  5.000). El backend lo asigna automáticamente.

## 6. Estructura de archivos

```
circulo/   (repo: Roberto6669/circulo)
├── app.py              Backend Flask: API + sirve el frontend
├── models.py           Esquema de la BD (Member con sponsor_id, Business, Offer, Coupon, Contact)
├── seed.py             Datos demo (incluye un árbol de referidos de ejemplo)
├── requirements.txt
├── render.yaml         Config de Render (crea web service + Postgres)
├── runtime.txt         Fija Python 3.12 en Render
├── Procfile            gunicorn app:app
├── .gitignore
├── README.md           Guía de instalación / despliegue
├── CLAUDE.md           ESTE archivo (estado del proyecto)
└── static/
    └── index.html      Frontend v1.9 (vanilla JS, single-file)
```

## 7. Cómo correr en local (Mac)

```bash
cd "$HOME/Library/Mobile Documents/com~apple~CloudDocs/__DATA/_AI/CIRCULO"
pip3 install Flask Flask-SQLAlchemy Flask-Cors Werkzeug --break-system-packages
python3 seed.py --reset
python3 app.py
```
Abre `http://127.0.0.1:5000`. (Local usa SQLite; no hace falta psycopg2 ni gunicorn.)

## 8. La API (contrato — para la Fase 2)

Base: la misma URL del sitio (llamadas relativas a `/api/...`). El token de login va en el header
`Authorization: Bearer <token>`.

| Método | Ruta | Para qué |
|---|---|---|
| POST | `/api/register/member` | Registrar miembro (acepta `referral_code`) |
| POST | `/api/register/business` | Registrar negocio |
| POST | `/api/login` | Login unificado (cliente o negocio) → `{token, role, profile}` |
| GET | `/api/me` | Perfil del usuario logueado |
| GET | `/api/referrals` | Referidos directos del miembro |
| GET | `/api/team` | Equipo completo + tamaño + niveles |
| GET | `/api/offers` | Catálogo de ofertas (público) |
| POST | `/api/offers` | Publicar oferta (negocio) |
| DELETE | `/api/offers/<id>` | Borrar oferta (negocio dueño) |
| GET | `/api/coupons/<code>` | Validar cupón |
| POST | `/api/contact` | Mensaje de contacto |
| GET | `/api/admin/stats` · `/members` · `/businesses` · `/contacts` · `/leaderboard` | Admin (header `X-Admin-Pin`) |
| POST | `/api/admin/coupons` | Generar cupones (admin) |

## 9. Credenciales demo (después de correr seed)

- **Cliente:** `cliente@demo.com` / `demo123` — tiene un equipo de 5 (María y Juan → Pedro, Ana, Luis).
- **Negocio:** `hola@habana1958.com` / `demo123` (y otros 4 negocios demo, todos con `demo123`).
- **Admin PIN:** `2026` (variable de entorno `ADMIN_PIN`).

## 10. Despliegue (Render)

- Repo en GitHub: **Roberto6669/circulo** (usuario `Roberto6669`, correo `roberto666@gmail.com`).
- En Render: **New → Blueprint** → repo `circulo` → lee `render.yaml` → crea `circulo-backend` (web)
  + `circulo-db` (Postgres) → **Apply**.
- Sembrar datos: Render → servicio `circulo-backend` → **Shell** → `python seed.py`.
- Verificar: `https://circulo-backend.onrender.com/health` → `{"ok": true}`.
- Variables de entorno: `DATABASE_URL` (lo pone Render solo), `SECRET_KEY` (lo genera Render), `ADMIN_PIN`.
- **De aquí en adelante, cada cambio es solo `git push`** y Render redespliega automáticamente.

## 11. El frontend (`static/index.html`) por dentro — v2.0, conectado al API

- **App de una sola página (SPA).** Vistas: `v-inicio`, `v-ofertas`, `v-carnet`, `v-negocios`,
  `v-admin`, `v-about`. Se cambian con `go(v)` que pone la clase `show` en `#v-<v>`.
- **Capa de datos (Fase 2):** objeto `API` (`API.get/post/put/del`) que hace `fetch` a `/api/...`,
  agrega el header `Authorization: Bearer <token>` si hay sesión, y `X-Admin-Pin` cuando se pasa `{pin}`.
  Las ofertas se cachean en `OFFERS` (cargadas con `loadOffers()` y normalizadas con `normOffer`).
- **Sesión:** objeto `Session = { token, role, profile }`. El token vive en `localStorage` (`circulo:token`);
  `init()` lo restaura llamando a `/api/me`. Helpers `curMember()`/`curBiz()` leen de `Session.role`.
  `setSession()` / `clearSession()` guardan/limpian. Login unificado: `doLogin(email, pass, alertId)`.
- **Funciones clave:** `registerMember()`, `registerBusiness()`, `loginMember()`, `loginBusiness()`,
  `logout()`, `saveMyData()` (→ `/api/me/update`), `publishOffer()` (POST/PUT), `deleteOffer()`,
  `validateMember()` (→ `/api/validate/<code>`), `renderCarnet()`, `renderBiz()`, `renderOffers()`,
  `renderAdmin()` (usa el PIN guardado en `adminPin`), `generateCoupons()`, `toggleCoupon()`.
- **Mapeo de campos API→UI:** la oferta del API trae `business`/`category`/`business_id`; `normOffer`
  los pasa a `biz`/`cat`/`bizId`. Los `id` de oferta ahora son **números** (no 'O1'): los `onclick`
  pasan el id sin comillas. El carnet usa `member_number` (no `num`) y `referral_code` para el QR.
- **Ofertas:** cada oferta tiene imagen (mitad superior); el negocio la sube y se redimensiona a 800×500
  en un canvas antes de guardar.
- **Admin:** PIN 2026; tablas de miembros/negocios (muestran usuario y contraseña), cupones, contacto.
- **About Us:** página con Educación financiera, Comunidad, Juegos, y beneficios de Fundadores.
- **Versión en el footer:** "Hecho por ROBERTO ESCOBAR CITTY · v1.X". **Sube el número de versión en
  cada cambio del frontend.**

## 12. Diseño / marca (para cualquier cambio visual)

- **Tema claro**, premium. Acentos en **oro** (`--gold`, `--gold-lt`). Fondo near-white (`--bg:#F5F4EF`).
- **Fuentes:** Fraunces (serif, títulos), Inter (cuerpo + h1 del hero), JetBrains Mono (números/códigos).
- **Títulos y botones en MAYÚSCULAS.** Esquinas poco redondeadas (`--radius:6px`). El carnet de membresía
  es dorado metálico (la pieza estrella del diseño).
- **Marca:** logo "C" dorado + "CÍRCULO / CLUB EXCLUSIVO". Nombre del autor + badge de versión en el footer.

## 13. ⭐ Entorno de Roberto y convenciones CRÍTICAS

**Computadoras (todas con el proyecto en iCloud, sincronizado):**
- Mac Mini M1 (`NEXT-LEVEL-Mac-mini-M1`)
- iMac M4 (`NEXT-LEVEL-iMac-M4`)
- MacBook Air M2

Para trabajar por Cowork, la app de escritorio de Claude debe estar instalada en la Mac que use en
ese momento, y debe **conectar (mount) la carpeta del proyecto**. Como todo vive en iCloud, este mismo
`CLAUDE.md` aparece en las tres máquinas: es la **fuente de verdad** del estado del proyecto, sin
importar desde cuál Mac se trabaje.

**Ubicación del proyecto (igual en todas, vía iCloud):**
```
~/Library/Mobile Documents/com~apple~CloudDocs/__DATA/_AI/CIRCULO
```

### Reparto de trabajo (Cowork como protagonista)

**Lo que hace Claude (tú) directamente, sin molestar a Roberto:**
- Leer y editar cualquier archivo del proyecto (Read/Write/Edit sobre la carpeta conectada).
- Correr y probar el backend en el **sandbox Linux** (Python, pip, gunicorn, curl).
- Hacer `git add` y `git commit` **locales** en la carpeta del proyecto.

**Lo que todavía necesita la Mac de Roberto (guíalo con comandos exactos):**
- **`git push` a GitHub** → las credenciales viven en su Mac, no en el sandbox. Tras commitear, dale
  el comando para que él pague el push (dispara el redeploy en Render).
- Ver la app en su propio navegador local, si lo desea.

**Probar el backend desde el sandbox (IMPORTANTE):** SQLite **falla con `disk I/O error`** si la base
se crea sobre la carpeta de iCloud montada. Copia el código a `/tmp` y prueba ahí:
```bash
T=/tmp/circulo_test
rm -rf "$T" && mkdir -p "$T/static"
SRC=<ruta-de-la-carpeta-montada-del-proyecto>
cp "$SRC"/app.py "$SRC"/models.py "$SRC"/seed.py "$T"/
cp "$SRC"/static/index.html "$T"/static/
cd "$T" && python3 seed.py --reset && python3 -m gunicorn app:app -b 127.0.0.1:5055 &
```
Luego prueba con `curl` (`/health`, `/`, `/api/offers`, `/api/login`). Verificado: arranca y responde OK.

**PROBLEMA CONOCIDO — iCloud traba git.** La carpeta `.git` se sincroniza y choca con git → error
*"Another git process is running / HEAD.lock"*, o warnings *"unable to unlink ... Operation not
permitted"* (son del sync; el commit igual se completa). **Workaround antes de cada commit/push:**
```bash
CIRCULO="$HOME/Library/Mobile Documents/com~apple~CloudDocs/__DATA/_AI/CIRCULO"
rm -f "$CIRCULO/.git/HEAD.lock" "$CIRCULO/.git/index.lock"
cd "$CIRCULO"
find . -type f -exec cat {} + > /dev/null 2>&1
git add -A
git commit -m "mensaje sin numeral"
git push
```
(El `find ... cat` fuerza a iCloud a descargar todos los archivos antes del push.)

**Reglas de oro:**
- **NUNCA** pongas comentarios con `#` dentro de los bloques de shell que Roberto vaya a pegar (su zsh los rompe).
- En su Mac, usa `pip3` y `--break-system-packages`.
- Local está en Python 3.14; Render en 3.12 (por `runtime.txt`).
- Cuando le toque algo a él: un paso a la vez, comandos exactos, y pídele que pegue el resultado.

---

**Resumen en una frase:** El backend Flask + Postgres y el frontend v2.0 ya están **conectados por el API**
(Fases 1 y 2 hechas); todo usa la base de datos real. El siguiente trabajo es la **Fase 3 — pantalla
"Mi equipo"** (link de referido + árbol del equipo, con `/api/team` y `/api/referrals` ya listos).
