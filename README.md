# Biwenger tracker

Sigue una liga de Biwenger: saldo de cada mánager, valor de su plantilla, todas sus operaciones
y la rentabilidad que ha sacado a cada fichaje. Se actualiza solo cada mañana y publica un
dashboard en GitHub Pages.

## Cómo funciona

Biwenger solo expone el saldo del usuario que se autentica. El de los rivales se **reconstruye**:

1. Tras un reset de liga, cada mánager arranca con `20.000.000 € − valor de su plantilla inicial`.
   La plantilla inicial se deduce del tablón: un jugador era del reparto si su dueño lo suelta
   sin haberlo fichado antes.
2. Sobre ese punto de partida se suman todos los movimientos de dinero: compras, ventas,
   cláusulas, intercambios, primas y bonus de jornada.
3. Cada ejecución se autocomprueba de dos formas. El saldo propio calculado debe coincidir con
   el que devuelve la API, y para cada mánager debe cumplirse:

   `patrimonio = 20.000.000 + premios − gasto en cláusulas + resultado de sus operaciones`

   Si algún día deja de cuadrar, el campo `descuadre` de `data/liga.json` deja de ser cero.

Dos detalles que costaron encontrar y conviene no perder:

- **Jornadas aplazadas.** Se liquidan dos veces. El segundo pago es el total recalculado y
  Biwenger retira el primero, así que sumar ambos infla el saldo.
- **Altas tardías.** Quien entra con la liga empezada recibe un lote de jugadores, algunos ya
  usados por otros. Su lote se valora en su fecha de alta, no en la del reset.

## Puesta en marcha

1. Crea `.env` a partir de `.env.example` con tu correo y contraseña de Biwenger.
2. `./run-daily.ps1` descarga los datos y escribe `data/*.json`.
3. `python -m scraper.dashboard` genera `docs/index.html`.

En GitHub hacen falta tres secretos del repositorio: `BIWENGER_EMAIL`, `BIWENGER_PASSWORD` y
`BIWENGER_LEAGUE_ID`. El fichero `.env` nunca se sube.

## Qué hay en cada sitio

| Ruta | Contenido |
|---|---|
| `scraper/client.py` | Autenticación y llamadas a la API |
| `scraper/fetch.py` | Descarga de liga, plantillas, tablón y precios |
| `scraper/balances.py` | Flujos de dinero y saldos |
| `scraper/initial.py` | Plantillas de partida y precios históricos |
| `scraper/trades.py` | Rentabilidad de cada operación |
| `scraper/series.py` | Patrimonio de cada día desde el reparto inicial |
| `scraper/daily.py` | Orquesta todo y escribe `data/` |
| `scraper/dashboard.py` | Genera `docs/index.html` |
| `data/historico.json` | Una foto por día; es lo que alimenta el gráfico de evolución |
