# CÍRCULO CLUB EXCLUSIVO

App de club de descuentos con membresía. Flask + SQLAlchemy.
Desplegada en Render: circulo-3qee.onrender.com
GitHub: Roberto6669

## Arquitectura
- Backend: Flask + SQLAlchemy
- Árbol de referidos estilo Primerica (sponsor referral tree)
- Lógica de referidos por BFS (búsqueda en anchura)
- Auth + leaderboard

## Estado actual
- **Fase 1 (backend):** en progreso — auth, BFS de referidos, leaderboard
- **Fase 2 (pendiente):** conectar el frontend al API
- **Fase 3 (pendiente):** pantalla "Mi equipo"

## Branding (aplicar consistente en todos los sitios)
- Header izquierda: logo (logoR.png) + "ROBERTO ESCOBAR CITTY" (mayúsculas, peso fuerte)
- Top derecha: badge de versión
- Footer: logo + nombre, centrado

## Preferencias de diseño
- Estética oscura y premium (HUD / Midnight Executive / editorial)
- Tipografía monoespaciada
- Presencia fuerte de marca

## Flujo de trabajo
- Iteración rápida con deploys frecuentes
- git push a GitHub → Render hace el deploy
- Repos activos viven en ~/Projects/ (fuera de iCloud)
- node_modules symlinkeado fuera de iCloud si aplica
