"""Alineaciones probables de la próxima jornada, desde FutbolFantasy.

Se usa FutbolFantasy y no JornadaPerfecta porque esta última prohíbe en su robots.txt el
acceso de rastreadores de IA (ClaudeBot, GPTBot). FutbolFantasy lo permite todo, y aun así
se accede identificándose y con una sola tanda de peticiones al día.

De cada jugador se saca el porcentaje de titularidad que publica la web. Cuando el once ya
está confirmado, la web deja de dar porcentaje y pasa a decir "Titular" o "Suplente";
ese caso se traduce a 100 y 0 y se marca como confirmado.
"""
import re
import time
import unicodedata
from datetime import datetime, timedelta

import requests

FUENTE = "https://www.futbolfantasy.com"
INDICE = FUENTE + "/laliga/posibles-alineaciones"
CABECERAS = {
    "User-Agent": "biwenger-tracker/1.0 (+https://github.com/JavatoJones/biwenger-tracker)",
    "Accept-Language": "es-ES,es;q=0.9",
}
DIAS = {"lun": 0, "mar": 1, "mie": 2, "mié": 2, "jue": 3, "vie": 4, "sab": 5, "sáb": 5, "dom": 6}


def normaliza(texto: str) -> str:
    """Minúsculas sin acentos ni signos, para poder comparar nombres entre webs."""
    sin = unicodedata.normalize("NFKD", str(texto))
    sin = "".join(c for c in sin if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", sin.lower()).strip("-")


def claves_equipos(teams: dict) -> set:
    """Todas las formas en que una web puede nombrar a cada equipo.

    FutbolFantasy acorta ('rayo'), Biwenger no ('Rayo Vallecano'), así que además del nombre
    y el slug se acepta la primera palabra cuando no la comparte ningún otro equipo.
    """
    claves, primeras = set(), {}
    for t in teams.values():
        for forma in (t.get("name"), t.get("slug")):
            if forma:
                claves.add(normaliza(forma))
        inicial = normaliza(t.get("name", "")).split("-")[0]
        primeras.setdefault(inicial, []).append(t["id"])
    claves |= {k for k, ids in primeras.items() if len(ids) == 1 and k}
    return claves


def _get(url: str) -> str:
    r = requests.get(url, headers=CABECERAS, timeout=40)
    r.raise_for_status()
    time.sleep(1.0)  # una petición por segundo: la web no nos necesita con prisa
    return r.text


def _cuando(texto: str, ahora: datetime):
    """Convierte 'Sab 16:15h' o 'Vie 09/10 21:00h' en una fecha concreta."""
    t = " ".join(texto.split())
    hora = re.search(r"(\d{1,2}):(\d{2})", t)
    if not hora:
        return None
    hh, mm = int(hora.group(1)), int(hora.group(2))
    dm = re.search(r"(\d{1,2})/(\d{1,2})", t)
    if dm:
        dia, mes = int(dm.group(1)), int(dm.group(2))
        año = ahora.year + (1 if mes < ahora.month - 6 else 0)
        return datetime(año, mes, dia, hh, mm)
    clave = normaliza(t.split()[0])[:3]
    if clave not in DIAS:
        return None
    falta = (DIAS[clave] - ahora.weekday()) % 7
    base = (ahora + timedelta(days=falta)).replace(hour=hh, minute=mm, second=0, microsecond=0)
    return base if base >= ahora - timedelta(hours=3) else base + timedelta(days=7)


PARTIDO = re.compile(
    r'<a href="' + re.escape(FUENTE) + r'/partidos/(\d+)-([a-z0-9-]+)"[^>]*'
    r'data-tooltip="([^"]*)".{0,1200}?<div class="fecha">\s*([^<]+?)\s*(?:<br>\s*([^<]+?)\s*)?</div>',
    re.S)


def partidos_de_la_jornada(html: str, equipos_liga: set, ahora: datetime) -> list:
    """Los partidos de LaLiga con la salida más próxima, que son los de la siguiente jornada."""
    vistos = {}
    for pid, slug, tooltip, d1, d2 in PARTIDO.findall(html):
        if pid in vistos:
            continue
        cuando = _cuando(f"{d1} {d2 or ''}", ahora)
        if not cuando or cuando < ahora - timedelta(hours=3):
            continue
        # El slug une los dos equipos; solo vale si ambos son de la competición.
        partes = slug.split("-")
        pareja = next(((" ".join(partes[:i]), " ".join(partes[i:]))
                       for i in range(1, len(partes))
                       if normaliza("-".join(partes[:i])) in equipos_liga
                       and normaliza("-".join(partes[i:])) in equipos_liga), None)
        if not pareja:
            continue
        nombres = [x.strip() for x in re.sub(r"\s\d+-\d+\s", " - ", tooltip).split(" - ")]
        vistos[pid] = {
            "id": pid, "url": f"{FUENTE}/partidos/{pid}-{slug}",
            "local": nombres[0] if nombres else pareja[0],
            "visitante": nombres[-1] if len(nombres) > 1 else pareja[1],
            "slug_local": normaliza("-".join(partes[:slug.split("-").index(partes[-1])] or partes[:1])),
            "fecha": cuando.isoformat(timespec="minutes"),
        }
    orden = sorted(vistos.values(), key=lambda p: p["fecha"])
    if not orden:
        return []
    # Una jornada cabe en cuatro días: lo que salga después ya es de la siguiente.
    corte = datetime.fromisoformat(orden[0]["fecha"]) + timedelta(days=4)
    return [p for p in orden if datetime.fromisoformat(p["fecha"]) <= corte][:10]


CAMPO = re.compile(r'<div class="([^"]*campo-wrapper[^"]*)"')
# El portero lleva su propia clase, y los suplentes se colocan en píxeles en vez de en
# porcentaje: eso es justo lo que distingue a quien sale en el campo de quien está fuera.
FICHA = re.compile(
    r'class="jugador_(\d+)\s+([^"]*?)camiseta-wrapper"\s*style="([^"]*)"[^>]*?data-onceFF="([a-z]+)"',
    re.S)


def once_del_partido(html: str) -> dict:
    """Jugadores de cada lado del campo, más el banquillo, con su probabilidad."""
    marcos = [(m.start(), " ".join(m.group(1).split())) for m in CAMPO.finditer(html)]
    bancos = [p for p, c in marcos if "suplentes" in c]

    def lado_de(pos: int) -> str:
        previos = [(p, c) for p, c in marcos if p <= pos]
        if not previos:
            return "?"
        p, c = previos[-1]
        if "suplentes" in c:  # los dos banquillos van en orden: primero local
            return "local" if bancos and p == bancos[0] else "visitante"
        return "local" if " local" in c else "visitante" if "visitante" in c else "?"

    salida = {"once_local": [], "once_visitante": [], "banquillo": [], "confirmado": False}
    fichas = list(FICHA.finditer(html))
    for n, m in enumerate(fichas):
        lado = lado_de(m.start())
        if lado not in ("local", "visitante"):
            continue
        clase, estilo = m.group(2), m.group(3)
        coords = re.search(r"left:\s*([\d.]+)%;\s*top:\s*([\d.]+)%", estilo)
        en_campo = bool(coords) and "supl-" not in clase

        # El bloque de un jugador acaba donde empieza el siguiente: así no se cuela su enlace.
        fin = fichas[n + 1].start() if n + 1 < len(fichas) else len(html)
        trozo = html[m.end(): fin]
        prob = re.search(r'data-probabilidad="([^"]*)"', trozo)
        crudo = (prob.group(1) if prob else "").strip()
        # La ficha del jugador lleva temporada; sin ella la ruta es genérica y no identifica.
        slug = re.search(r"/jugadores/([a-z0-9-]+)/[a-z]+-\d+-\d+", trozo)
        pct = re.match(r"(\d{1,3})\s*%", crudo)
        if pct:
            probabilidad = int(pct.group(1))
        else:
            probabilidad = 100 if normaliza(crudo).startswith("titular") else 0
            salida["confirmado"] = salida["confirmado"] or bool(crudo)

        jugador = {
            "ff_id": int(m.group(1)), "slug": slug.group(1) if slug else None,
            "titular": m.group(4) == "titular", "probabilidad": probabilidad,
            "etiqueta": crudo or None, "portero": "portero" in clase, "lado": lado,
        }
        if en_campo:
            jugador["x"], jugador["y"] = float(coords.group(1)), float(coords.group(2))
            salida["once_" + lado].append(jugador)
        else:
            salida["banquillo"].append(jugador)

    for lado in ("once_local", "once_visitante"):
        salida[lado].sort(key=lambda j: (j["y"], j["x"]))
    salida["banquillo"].sort(key=lambda j: -j["probabilidad"])
    return salida


def enlazar_con_biwenger(datos: dict, players: dict, teams: dict, duenos: dict) -> dict:
    """Añade a cada jugador su ficha de Biwenger y el mánager que lo tiene.

    El emparejamiento se hace solo entre los dos equipos del partido, así un apellido
    repetido en la liga no puede confundirse con otro.
    """
    por_equipo: dict[int, list] = {}
    for p in players.values():
        por_equipo.setdefault(p.get("teamID"), []).append(p)
    id_equipo, primeras = {}, {}
    for t in teams.values():
        for clave in (t.get("name"), t.get("slug")):
            if clave:
                id_equipo[normaliza(clave)] = t["id"]
        primeras.setdefault(normaliza(t.get("name", "")).split("-")[0], []).append(t["id"])
    for clave, ids in primeras.items():
        if len(ids) == 1 and clave:
            id_equipo.setdefault(clave, ids[0])

    def busca(slug: str, equipo_id):
        if not slug or equipo_id is None:
            return None
        base = re.sub(r"-\d+$", "", normaliza(slug))  # quita el sufijo de desambiguación
        plantilla = por_equipo.get(equipo_id, [])
        exactos = [p for p in plantilla if normaliza(p["name"]) == base
                   or re.sub(r"^[a-z]-", "", normaliza(p.get("slug", ""))) == base]
        if len(exactos) == 1:
            return exactos[0]
        cola = base.split("-")[-1]
        porcola = [p for p in plantilla if normaliza(p["name"]).split("-")[-1] == cola]
        return porcola[0] if len(porcola) == 1 else None

    enlazados = fallidos = 0
    for partido in datos["partidos"]:
        equipos = {"local": id_equipo.get(normaliza(partido["local"])),
                   "visitante": id_equipo.get(normaliza(partido["visitante"]))}
        partido["equipo_local_id"], partido["equipo_visitante_id"] = equipos["local"], equipos["visitante"]
        for grupo in ("once_local", "once_visitante", "banquillo"):
            for j in partido[grupo]:
                ficha = busca(j["slug"], equipos.get(j["lado"]))
                if ficha:
                    enlazados += 1
                    dueno = duenos.get(ficha["id"])
                    j.update({"id": ficha["id"], "nombre": ficha["name"],
                              "precio": ficha.get("price"), "puntos": ficha.get("points"),
                              "dueno": dueno[0] if dueno else None,
                              "dueno_nombre": dueno[1] if dueno else None})
                else:
                    fallidos += 1
                    j["nombre"] = (j["slug"] or f"#{j['ff_id']}").replace("-", " ").title()
    datos["enlazados"], datos["sin_enlazar"] = enlazados, fallidos
    return datos


def descargar(equipos_liga: set, ahora: datetime | None = None) -> dict:
    """Devuelve {jornada, actualizado, partidos:[...]} o levanta la excepción de red."""
    ahora = ahora or datetime.now()
    indice = _get(INDICE)
    titulo = re.search(r"Jornada\s*(\d+)", indice)
    partidos = partidos_de_la_jornada(indice, equipos_liga, ahora)
    for p in partidos:
        p.update(once_del_partido(_get(p["url"])))
        p.pop("slug_local", None)
    return {
        "jornada": int(titulo.group(1)) if titulo else None,
        "actualizado": ahora.isoformat(timespec="minutes"),
        "fuente": INDICE,
        "partidos": partidos,
    }
