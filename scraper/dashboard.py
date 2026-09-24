"""Genera dashboard.html con los datos embebidos.

Uso: python -m scraper.dashboard
"""
import json
from datetime import datetime
from pathlib import Path

from .fetch import RAW

DATA = RAW.parent
OUT = DATA.parent / "docs" / "index.html"  # GitHub Pages sirve la carpeta docs/


def _fecha(ts):
    return datetime.fromtimestamp(ts).strftime("%d/%m") if ts else None


def build() -> Path:
    liga = json.loads((DATA / "liga.json").read_text(encoding="utf-8"))
    ops = json.loads((DATA / "operaciones.json").read_text(encoding="utf-8"))
    hist = json.loads((DATA / "historico.json").read_text(encoding="utf-8"))

    cerradas = [{
        "u": t["user"], "j": t["jugador"], "c": t["cost"], "v": t["revenue"], "p": t["profit"],
        "ein": t["how_in"], "eout": t["how_out"], "din": _fecha(t["date_in"]), "dout": _fecha(t["date_out"]),
    } for t in ops["cerradas"] if t["profit"] is not None]
    abiertas = [{
        "u": p["user"], "j": p["jugador"], "c": p["cost"], "v": p["valor_hoy"], "p": p["latente"],
        "ein": p["how_in"], "din": _fecha(p["date_in"]),
    } for p in ops["abiertas"]]

    # La gráfica solo necesita fechas y patrimonio por equipo, en columnas paralelas.
    fechas = [d["fecha"] for d in hist]
    series = {u["id"]: [] for u in liga["usuarios"]}
    for dia in hist:
        del_dia = {x["id"]: x["patrimonio"] for x in dia["usuarios"]}
        for uid in series:
            series[uid].append(del_dia.get(uid))

    # Alineaciones: solo lo que pinta la web, sin los identificadores de la fuente.
    ruta_alin = DATA / "alineaciones.json"
    alin = json.loads(ruta_alin.read_text(encoding="utf-8")) if ruta_alin.exists() else None
    if alin:
        util = ("nombre", "probabilidad", "titular", "etiqueta", "dueno", "dueno_nombre", "x", "y")
        for p in alin["partidos"]:
            for g in ("once_local", "once_visitante", "banquillo"):
                p[g] = [{k: j[k] for k in util if k in j} for j in p[g]]

    payload = {
        "liga": liga["liga"], "actualizado": liga["actualizado"], "yo": liga["usuario_propio"],
        "usuarios": liga["usuarios"], "cerradas": cerradas, "abiertas": abiertas,
        "evolucion": {"fechas": fechas, "series": series},
        "alineaciones": alin,
    }
    html = PLANTILLA.replace("__DATOS__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


PLANTILLA = r"""<title>Fantacis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;500;600&family=Archivo+Narrow:wght@500;600;700&display=swap">
<style>
:root{
  --plano:#f3f5f3; --tarjeta:#fcfcfb; --hueco:#e9ebe8;
  --tinta:#0b0b0b; --tinta-2:#52514e; --tinta-3:#7c817d;
  --linea:#e1e3df; --borde:rgba(11,11,11,.10); --eje:#c3c2b7;
  --acento:#2a78d6;
  --serie-1:#2a78d6; --serie-2:#eb6834; --serie-3:#1baf7a; --serie-4:#eda100;
  --serie-5:#e87ba4; --serie-6:#008300; --serie-7:#4a3aa7; --serie-8:#e34948;
  --sube:#0a7d0a; --baja:#c23636; --sube-f:rgba(10,125,10,.12); --baja-f:rgba(194,54,54,.12);
  --cesped:#e9efe9; --cesped-raya:rgba(11,11,11,.13);
  --radio:10px;
  --sans:"Archivo",system-ui,-apple-system,"Segoe UI",sans-serif;
  --titular:"Archivo Narrow","Archivo Narrow Fallback",system-ui,sans-serif;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --plano:#0c0e0d; --tarjeta:#1a1a19; --hueco:#232523;
  --tinta:#f4f5f3; --tinta-2:#c3c2b7; --tinta-3:#898781;
  --linea:#2c2c2a; --borde:rgba(255,255,255,.10); --eje:#383835;
  --acento:#3987e5;
  --serie-1:#3987e5; --serie-2:#d95926; --serie-3:#199e70; --serie-4:#c98500;
  --serie-5:#d55181; --serie-6:#008300; --serie-7:#9085e9; --serie-8:#e66767;
  --sube:#2cb72c; --baja:#e66767; --sube-f:rgba(44,183,44,.16); --baja-f:rgba(230,103,103,.16);
  --cesped:#182018; --cesped-raya:rgba(255,255,255,.13);
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --plano:#0c0e0d; --tarjeta:#1a1a19; --hueco:#232523;
  --tinta:#f4f5f3; --tinta-2:#c3c2b7; --tinta-3:#898781;
  --linea:#2c2c2a; --borde:rgba(255,255,255,.10); --eje:#383835;
  --acento:#3987e5;
  --serie-1:#3987e5; --serie-2:#d95926; --serie-3:#199e70; --serie-4:#c98500;
  --serie-5:#d55181; --serie-6:#008300; --serie-7:#9085e9; --serie-8:#e66767;
  --sube:#2cb72c; --baja:#e66767; --sube-f:rgba(44,183,44,.16); --baja-f:rgba(230,103,103,.16);
  --cesped:#182018; --cesped-raya:rgba(255,255,255,.13);
  color-scheme:dark;
}
*{box-sizing:border-box}
body{margin:0;background:var(--plano);color:var(--tinta);font-family:var(--sans);font-size:15px;line-height:1.5;-webkit-text-size-adjust:100%}
.envoltura{max-width:1140px;margin:0 auto;padding-block:28px 64px;padding-left:20px;padding-right:20px}
h1,h2,h3{font-family:var(--titular);font-weight:700;text-wrap:balance;margin:0;letter-spacing:.01em}
h1{font-size:clamp(34px,6vw,50px);line-height:1}
h2{font-size:22px}
.num{font-variant-numeric:tabular-nums}
.rotulo{font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--tinta-3);font-weight:600}
.pos{color:var(--sube)} .neg{color:var(--baja)}

/* Cabecera */
header{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-end;justify-content:space-between;
  border-bottom:2px solid var(--tinta);padding-bottom:14px;margin-bottom:8px}
.sub{color:var(--tinta-2);font-size:14px;margin-top:4px}
.sello{display:inline-flex;align-items:center;gap:7px;background:var(--sube-f);color:var(--sube);
  border-radius:999px;padding:5px 12px;font-size:12.5px;font-weight:600}
.sello svg{flex:none}
.acciones{display:flex;gap:8px;align-items:center}
button{font-family:inherit;font-size:13px;color:var(--tinta-2);background:var(--tarjeta);
  border:1px solid var(--borde);border-radius:8px;padding:7px 12px;cursor:pointer}
button:hover{color:var(--tinta);border-color:var(--eje)}
button:focus-visible{outline:2px solid var(--acento);outline-offset:2px}
/* Solo los botones que alternan vista se invierten. Ojo: si esto se aplicara a todo
   `button[aria-pressed]` también pintaría las filas de la tabla, que también son botones,
   y su texto quedaría del color del fondo. */
.alterna[aria-pressed="true"]{background:var(--tinta);color:var(--plano);border-color:var(--tinta)}

section{margin-top:40px}
.encabezado-seccion{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline;justify-content:space-between;margin-bottom:14px}
.nota{color:var(--tinta-3);font-size:13px;max-width:62ch}

/* Clasificación */
.tabla{background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio);overflow:hidden}
#clasificacion table{min-width:auto}
#clasificacion th{cursor:pointer;user-select:none;white-space:nowrap}
#clasificacion th:hover{color:var(--tinta)}
#clasificacion th[aria-sort]{color:var(--tinta)}
#clasificacion th .flecha{margin-left:4px;font-size:10px}
#clasificacion tr[data-id]{cursor:pointer}
#clasificacion tr[aria-selected="true"]{background:var(--hueco)}
#clasificacion tr[aria-selected="true"] td:first-child{box-shadow:inset 3px 0 0 var(--acento)}
#clasificacion tr:focus-visible{outline:2px solid var(--acento);outline-offset:-2px}
/* La celda de la métrica ordenada lleva su propia barra de fondo, así la comparación
   visual viaja con la columna elegida en vez de ocupar una columna fija. */
.celda-barra{position:relative}
.celda-barra .relleno{position:absolute;left:0;top:3px;bottom:3px;border-radius:2px;
  background:var(--acento);opacity:.16}
.celda-barra.neg .relleno{background:var(--baja);opacity:.22}
.celda-barra .cifra{position:relative}
.puesto{font-family:var(--titular);font-size:17px;color:var(--tinta-3);font-weight:600}
.equipo{font-family:var(--titular);font-size:17px;font-weight:600;line-height:1.15;overflow-wrap:anywhere}
/* Próxima jornada */
.jor-partido{background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio);
  padding:14px 16px;margin-bottom:12px}
.jor-cab{display:flex;flex-wrap:wrap;gap:6px 12px;align-items:baseline;justify-content:space-between;margin-bottom:12px}
.jor-equipos{font-family:var(--titular);font-size:17px;font-weight:600}
.jor-meta{font-size:12.5px;color:var(--tinta-3)}
.insignia{font-size:10.5px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;
  border:1px solid var(--borde);border-radius:999px;padding:2px 8px;color:var(--tinta-2)}
.campos{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.campo{position:relative;aspect-ratio:3/4;border-radius:8px;overflow:hidden;
  background:var(--cesped);border:1px solid var(--borde)}
.campo .raya{position:absolute;border:1px solid var(--cesped-raya);border-radius:2px}
.campo .medio{left:0;right:0;top:50%;border-width:1px 0 0 0;border-radius:0}
.campo .area{left:22%;right:22%;bottom:0;height:16%;border-bottom:0}
.campo .circulo{left:50%;top:50%;width:26%;aspect-ratio:1;transform:translate(-50%,-50%);border-radius:50%}
.pieza{position:absolute;transform:translate(-50%,-50%);width:74px;text-align:center;line-height:1.15}
.ficha-jug{width:26px;height:26px;margin:0 auto;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:10.5px;font-weight:600;font-variant-numeric:tabular-nums;
  background:var(--tarjeta);border:2px solid var(--eje);color:var(--tinta-2)}
.pieza.libre .ficha-jug{border-style:dashed}
.pieza.mio .ficha-jug{border-color:var(--acento);background:var(--acento);color:#fff}
.pieza.rival .ficha-jug{border-color:var(--serie-2);color:var(--tinta)}
.pieza .etq{font-size:10px;margin-top:2px;color:var(--tinta-2);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.pieza .quien{font-size:9px;color:var(--tinta-3);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.jor-resumen{background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio);
  padding:14px 16px;margin-bottom:14px}
.jor-resumen ul{list-style:none;margin:8px 0 0;padding:0;display:grid;
  grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:6px 14px}
.jor-resumen li{display:flex;justify-content:space-between;gap:10px;font-size:13px;
  border-bottom:1px solid var(--linea);padding-bottom:4px}
@media (max-width:640px){.campos{grid-template-columns:1fr}.pieza{width:62px}}

/* Filtros de la gráfica */
.fichas{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:16px}
.ficha{display:inline-flex;align-items:center;gap:7px;font-size:12.5px;padding:5px 11px;
  border:1px solid var(--borde);border-radius:999px;background:var(--tarjeta);color:var(--tinta-3);cursor:pointer}
.ficha:hover{color:var(--tinta)}
.ficha[aria-pressed="true"]{color:var(--tinta);border-color:var(--eje);background:var(--hueco)}
.ficha svg{flex:none;opacity:.3}
.ficha[aria-pressed="true"] svg{opacity:1}
.mandos{display:flex;gap:8px;margin-bottom:12px}
.lienzo{position:relative}
.globo{position:absolute;pointer-events:none;background:var(--tarjeta);border:1px solid var(--eje);
  border-radius:8px;padding:9px 11px;font-size:12.5px;box-shadow:0 4px 14px rgba(0,0,0,.14);
  min-width:168px;z-index:2}
.globo b{font-family:var(--titular);font-size:13px;display:block;margin-bottom:5px}
.globo div{display:flex;align-items:center;gap:7px;justify-content:space-between;line-height:1.7}
.globo span:first-child{display:inline-flex;align-items:center;gap:6px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.der{text-align:right}
/* `display:block` es imprescindible: son <span>, y en un elemento en línea el alto y el
   ancho se ignoran, así que la barra no se veía. */
.barra{display:block;height:9px;border-radius:3px 4px 4px 3px;background:var(--acento);min-width:3px}
.pista{display:block;background:var(--hueco);border-radius:4px;height:9px;overflow:hidden}
.pie-tabla{padding:10px 16px;border-top:1px solid var(--linea);color:var(--tinta-3);font-size:12.5px}

/* Gráfico divergente */
.marco{background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio);padding:18px 16px}
.leyenda{display:flex;gap:16px;flex-wrap:wrap;font-size:13px;color:var(--tinta-2);margin-bottom:14px}
.llave{display:inline-flex;align-items:center;gap:7px}
.muestra{width:11px;height:11px;border-radius:3px;flex:none}
.filas-div{display:grid;gap:4px}
.fila-div{display:grid;grid-template-columns:minmax(96px,150px) 1fr;gap:12px;align-items:center;
  font-size:13px;padding:4px 6px;border-radius:7px;cursor:default}
.fila-div:hover{background:var(--hueco)}
.pista-div{position:relative;height:32px}
.cero{position:absolute;top:0;bottom:0;width:1px;background:var(--eje)}
.marca{position:absolute;height:8px;border-radius:2px}
.marca.j{top:2px;background:var(--serie-3)}
.marca.r{top:12px;background:var(--serie-1)}
.marca.l{top:22px;background:var(--serie-2)}
.globo .total{border-top:1px solid var(--linea);margin-top:6px;padding-top:6px;font-weight:600}

/* Detalle */
.rejilla-detalle{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin-bottom:18px}
.baldosa{background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio);padding:14px 16px}
.baldosa .valor{font-family:var(--titular);font-size:27px;font-weight:700;line-height:1.1;margin-top:5px}
.baldosa .pie{font-size:12px;color:var(--tinta-3);margin-top:3px}
.envoltura-tabla{overflow-x:auto;background:var(--tarjeta);border:1px solid var(--borde);border-radius:var(--radio)}
table{border-collapse:collapse;width:100%;min-width:620px;font-size:13.5px}
th{text-align:left;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--tinta-3);
  font-weight:600;padding:10px 14px;background:var(--hueco);border-bottom:1px solid var(--linea);white-space:nowrap}
td{padding:9px 14px;border-top:1px solid var(--linea);vertical-align:middle}
tbody tr:hover{background:var(--hueco)}
.jugador{font-weight:500}
.via{display:inline-block;font-size:11px;color:var(--tinta-2);background:var(--hueco);
  border:1px solid var(--borde);border-radius:4px;padding:1px 6px;white-space:nowrap}
.vacio{padding:26px 16px;text-align:center;color:var(--tinta-3);font-size:13.5px}

/* Evolución */
.grafico{width:100%;height:auto;display:block}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--linea);color:var(--tinta-3);font-size:12.5px}
@media (max-width:720px){
  .fila-div{grid-template-columns:minmax(78px,110px) 1fr;font-size:12px}
  #clasificacion td,#clasificacion th{padding-left:10px;padding-right:10px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>

<div class="envoltura">
  <header>
    <div>
      <h1 id="nombre-liga">Fantacis</h1>
      <p class="sub">Saldos, patrimonios y rentabilidad de cada fichaje · <span id="sello-fecha"></span></p>
    </div>
    <div class="acciones">
      <span class="sello" id="sello-ok"></span>
      <button id="tema" type="button" title="Cambiar tema">Tema</button>
    </div>
  </header>

  <section id="s-clasificacion">
    <div class="encabezado-seccion">
      <h2>Clasificación</h2>
      <p class="nota">Elige qué conceptos ver y pulsa una cabecera para ordenar. Pulsa un equipo para ver sus operaciones.</p>
    </div>
    <div class="fichas" id="cl-columnas"></div>
    <div class="tabla">
      <div class="envoltura-tabla" style="border:0;border-radius:0"><div id="clasificacion"></div></div>
      <div class="pie-tabla" id="pie-clasificacion"></div>
    </div>
  </section>

  <section id="s-evolucion">
    <div class="encabezado-seccion">
      <h2>Evolución del patrimonio</h2>
      <p class="nota">Reconstruido día a día desde el reparto inicial. Elige qué equipos comparar.</p>
    </div>
    <div class="marco">
      <div class="mandos">
        <button type="button" class="alterna" id="ev-todos">Todos</button>
        <button type="button" class="alterna" id="ev-ninguno">Ninguno</button>
        <button type="button" class="alterna" id="ev-podio">Los cuatro primeros</button>
      </div>
      <div class="fichas" id="ev-fichas"></div>
      <div class="lienzo" id="ev-lienzo"></div>
    </div>
  </section>

  <section id="s-resultado">
    <div class="encabezado-seccion">
      <h2>De dónde sale el dinero</h2>
      <p class="nota">Tres fuentes distintas: lo cobrado por rendimiento en las jornadas, lo embolsado
        vendiendo jugadores y lo que todavía está metido en la plantilla.</p>
    </div>
    <div class="marco">
      <div class="mandos" id="res-orden"></div>
      <div class="leyenda">
        <span class="llave"><span class="muestra" style="background:var(--serie-3)"></span>Bonus de jornada</span>
        <span class="llave"><span class="muestra" style="background:var(--serie-1)"></span>Realizado, ventas cerradas</span>
        <span class="llave"><span class="muestra" style="background:var(--serie-2)"></span>Latente, plantilla actual</span>
      </div>
      <div class="lienzo">
        <div class="filas-div" id="divergente"></div>
        <div class="globo" id="res-globo" style="display:none"></div>
      </div>
    </div>
  </section>

  <section id="s-jornada">
    <div class="encabezado-seccion">
      <h2 id="jor-titulo">Próxima jornada</h2>
      <p class="nota">Onces probables de <a href="https://www.futbolfantasy.com/laliga/posibles-alineaciones"
        target="_blank" rel="noopener">FutbolFantasy</a>. Cuando aún hay dudas publican un porcentaje;
        cuando se deciden, marcan el once como definitivo.</p>
    </div>
    <div id="jor-resumen"></div>
    <div class="mandos" id="jor-filtro">
      <button type="button" class="alterna" data-jor="mios" aria-pressed="true">Solo mis jugadores</button>
      <button type="button" class="alterna" data-jor="liga" aria-pressed="false">Los de la liga</button>
      <button type="button" class="alterna" data-jor="todos" aria-pressed="false">Todos</button>
    </div>
    <div id="jor-partidos"></div>
  </section>

  <section id="s-detalle">
    <div class="encabezado-seccion">
      <h2 id="titulo-detalle">Detalle</h2>
      <div class="acciones">
        <button type="button" class="alterna" id="btn-cerradas" aria-pressed="true">Operaciones cerradas</button>
        <button type="button" class="alterna" id="btn-abiertas" aria-pressed="false">Plantilla actual</button>
      </div>
    </div>
    <div class="rejilla-detalle" id="baldosas"></div>
    <div class="envoltura-tabla"><div id="tabla-detalle"></div></div>
  </section>

  <footer>
    Datos de Biwenger, liga <span id="pie-liga"></span>. El saldo propio se contrasta contra el que devuelve
    Biwenger; el de los rivales se reconstruye operación a operación desde el reparto inicial y cuadra al céntimo
    con su patrimonio.
  </footer>
</div>

<script id="datos" type="application/json">__DATOS__</script>
<script>
(function(){
  "use strict";
  var D = JSON.parse(document.getElementById("datos").textContent);
  var U = D.usuarios, porId = {};
  U.forEach(function(u){ porId[u.id] = u; });
  var sel = D.yo, vista = "cerradas";

  var MENOS = "−";
  function eur(n){
    var s = n < 0 ? MENOS : "";
    return s + Math.abs(Math.round(n)).toLocaleString("es-ES") + " €";
  }
  function eurFirmado(n){
    if (!n) return "0 €";
    return (n > 0 ? "+" : MENOS) + Math.abs(Math.round(n)).toLocaleString("es-ES") + " €";
  }
  function millones(n){
    var s = n < 0 ? MENOS : "";
    return s + (Math.abs(n)/1e6).toLocaleString("es-ES",{minimumFractionDigits:1,maximumFractionDigits:1}) + " M€";
  }
  function clase(n){ return n > 0 ? "pos" : n < 0 ? "neg" : ""; }
  function esc(s){ return String(s).replace(/[&<>"]/g, function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]; }); }

  // Cabecera
  document.getElementById("nombre-liga").textContent = D.liga;
  document.getElementById("pie-liga").textContent = D.liga;
  var f = D.actualizado.split("-");
  document.getElementById("sello-fecha").textContent = "actualizado el " + f[2] + "/" + f[1] + "/" + f[0];
  var yo = porId[D.yo];
  document.getElementById("sello-ok").innerHTML =
    '<svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true">' +
    '<path d="M2 8.5l4 4 8-9" fill="none" stroke="currentColor" stroke-width="2.4" ' +
    'stroke-linecap="round" stroke-linejoin="round"/></svg>' +
    (yo && yo.saldo_verificado ? "Saldo verificado" : "Saldo sin verificar");

  // Clasificación: columnas elegibles y ordenación por cualquiera de ellas
  var COLS = [
    {k:"patrimonio",     t:"Patrimonio", d:"Saldo más valor de la plantilla"},
    {k:"saldo",          t:"Efectivo",   d:"Dinero disponible en caja", firma:true},
    {k:"valor_equipo",   t:"Plantilla",  d:"Valor de mercado de sus jugadores"},
    {k:"realizado",      t:"Realizado",  d:"Ganado en las ventas ya cerradas", firma:true},
    {k:"latente",        t:"Latente",    d:"Lo que ganaría vendiendo hoy su plantilla", firma:true},
    {k:"bonus_jornadas", t:"Bonus",      d:"Cobrado por rendimiento en las jornadas"},
    {k:"puntos",         t:"Puntos",     d:"Puntos de la clasificación oficial", plano:true}
  ];
  var visiblesCol = {patrimonio:true, saldo:true, valor_equipo:true, bonus_jornadas:true};
  var ordenPor = "patrimonio", ordenAsc = false;

  document.getElementById("cl-columnas").innerHTML = COLS.map(function(c){
    return '<button type="button" class="ficha" data-col="' + c.k + '" title="' + esc(c.d) + '" ' +
      'aria-pressed="' + !!visiblesCol[c.k] + '">' + c.t + '</button>';
  }).join("");

  function pintarClasificacion(){
    var cols = COLS.filter(function(c){ return visiblesCol[c.k]; });
    if (!cols.length){ visiblesCol.patrimonio = true; cols = [COLS[0]];
      document.querySelector('[data-col="patrimonio"]').setAttribute("aria-pressed", "true"); }
    if (!visiblesCol[ordenPor]) ordenPor = cols[0].k;

    var filas = U.slice().sort(function(a,b){
      return (ordenAsc ? 1 : -1) * (a[ordenPor] - b[ordenPor]); });
    var tope = Math.max.apply(null, U.map(function(u){ return Math.abs(u[ordenPor]); })) || 1;

    var cab = '<tr><th style="cursor:default">#</th><th style="cursor:default">Equipo</th>' +
      cols.map(function(c){
        var act = c.k === ordenPor;
        return '<th class="der" data-orden="' + c.k + '"' + (act ? ' aria-sort="' +
          (ordenAsc ? "ascending" : "descending") + '"' : '') + ' title="' + esc(c.d) + '">' + c.t +
          (act ? '<span class="flecha">' + (ordenAsc ? "▲" : "▼") + '</span>' : '') + '</th>';
      }).join("") + '</tr>';

    var cuerpo = filas.map(function(u, i){
      var celdas = cols.map(function(c){
        var v = u[c.k];
        var texto = c.plano ? v.toLocaleString("es-ES") : (c.firma ? eurFirmado(v) : eur(v));
        if (c.k !== ordenPor)
          return '<td class="der num ' + (c.firma ? clase(v) : "") + '">' + texto + '</td>';
        return '<td class="der num celda-barra ' + (v < 0 ? "neg" : "") + '" style="font-weight:600">' +
          '<span class="relleno" style="width:' + (Math.abs(v) / tope * 100).toFixed(1) + '%"></span>' +
          '<span class="cifra ' + (c.firma ? clase(v) : "") + '">' + texto + '</span></td>';
      }).join("");
      return '<tr data-id="' + u.id + '" tabindex="0" role="button" aria-selected="' + (u.id === sel) + '">' +
        '<td class="puesto num">' + (i + 1) + '</td>' +
        '<td class="equipo">' + esc(u.nombre) + '</td>' + celdas + '</tr>';
    }).join("");

    document.getElementById("clasificacion").innerHTML =
      '<table><thead>' + cab + '</thead><tbody>' + cuerpo + '</tbody></table>';
  }

  document.getElementById("cl-columnas").addEventListener("click", function(e){
    var b = e.target.closest("[data-col]");
    if (!b) return;
    var k = b.dataset.col;
    visiblesCol[k] = !visiblesCol[k];
    b.setAttribute("aria-pressed", !!visiblesCol[k]);
    pintarClasificacion();
  });
  pintarClasificacion();
  var enRojo = U.filter(function(u){ return u.saldo < 0; }).length;
  document.getElementById("pie-clasificacion").textContent =
    U.length + " equipos · " + enRojo + " con el saldo en números rojos · " +
    "diferencia entre el primero y el último: " + eur(U[0].patrimonio - U[U.length-1].patrimonio);

  // De dónde sale el dinero
  var FUENTES = [
    {k:"bonus_jornadas", cls:"j", t:"Bonus de jornada", col:"var(--serie-3)"},
    {k:"realizado",      cls:"r", t:"Realizado",        col:"var(--serie-1)"},
    {k:"latente",        cls:"l", t:"Latente",          col:"var(--serie-2)"}
  ];
  var suma = function(u){ return u.bonus_jornadas + u.realizado + u.latente; };
  var ordenRes = "total";
  document.getElementById("res-orden").innerHTML =
    '<button type="button" class="alterna" data-res="total" aria-pressed="true">Total</button>' +
    FUENTES.map(function(f){
      return '<button type="button" class="alterna" data-res="' + f.k + '" aria-pressed="false">' +
        f.t + '</button>';
    }).join("");

  function pintarFuentes(){
    var clave = function(u){ return ordenRes === "total" ? suma(u) : u[ordenRes]; };
    var tope = Math.max.apply(null, U.map(function(u){
      return Math.max.apply(null, FUENTES.map(function(f){ return Math.abs(u[f.k]); })); })) || 1;
    var filas = U.slice().sort(function(a,b){ return clave(b) - clave(a); });
    document.getElementById("divergente").innerHTML = filas.map(function(u){
      var marcas = FUENTES.map(function(f){
        var v = u[f.k], ancho = Math.abs(v) / tope * 50;
        return '<span class="marca ' + f.cls + '" style="left:' +
          (v >= 0 ? 50 : 50 - ancho).toFixed(2) + '%;width:' + Math.max(0.4, ancho).toFixed(2) + '%"></span>';
      }).join("");
      return '<div class="fila-div" data-res-id="' + u.id + '">' +
        '<span style="overflow-wrap:anywhere">' + esc(u.nombre) + '</span>' +
        '<span class="pista-div"><span class="cero" style="left:50%"></span>' + marcas + '</span></div>';
    }).join("");
  }

  var globoRes = document.getElementById("res-globo");
  document.getElementById("divergente").addEventListener("mousemove", function(e){
    var fila = e.target.closest("[data-res-id]");
    if (!fila){ globoRes.style.display = "none"; return; }
    var u = porId[Number(fila.dataset.resId)];
    globoRes.innerHTML = '<b>' + esc(u.nombre) + '</b>' + FUENTES.map(function(f){
      return '<div><span><span class="muestra" style="background:' + f.col + '"></span>' + f.t +
        '</span><span class="num ' + clase(u[f.k]) + '">' + eurFirmado(u[f.k]) + '</span></div>';
    }).join("") + '<div class="total"><span>Suma</span><span class="num ' + clase(suma(u)) +
      '">' + eurFirmado(suma(u)) + '</span></div>';
    globoRes.style.display = "";
    // El globo se posiciona dentro de .lienzo, así que las coordenadas van contra ese marco.
    var caja = globoRes.parentElement.getBoundingClientRect();
    var x = e.clientX - caja.left + 16, y = e.clientY - caja.top + 14;
    globoRes.style.left = Math.min(x, caja.width - globoRes.offsetWidth - 6) + "px";
    globoRes.style.top = Math.min(y, caja.height - globoRes.offsetHeight - 2) + "px";
  });
  document.getElementById("divergente").addEventListener("mouseleave", function(){
    globoRes.style.display = "none";
  });
  document.getElementById("res-orden").addEventListener("click", function(e){
    var b = e.target.closest("[data-res]");
    if (!b) return;
    ordenRes = b.dataset.res;
    this.querySelectorAll("[data-res]").forEach(function(x){
      x.setAttribute("aria-pressed", x.dataset.res === ordenRes); });
    pintarFuentes();
  });
  pintarFuentes();

  // Detalle
  function pintarDetalle(){
    var u = porId[sel];
    document.getElementById("titulo-detalle").textContent = u.nombre;
    var abiertas = D.abiertas.filter(function(t){ return t.u === sel; });
    var cerradas = D.cerradas.filter(function(t){ return t.u === sel; });
    var aciertos = cerradas.filter(function(t){ return t.p > 0; }).length;

    document.getElementById("baldosas").innerHTML = [
      ["Patrimonio", millones(u.patrimonio), "puesto " + u.posicion + " de " + U.length + " · " + u.puntos + " puntos", ""],
      ["Saldo en caja", eur(u.saldo), "empezó con " + eur(u.saldo_inicial), clase(u.saldo)],
      ["Ganado operando", eurFirmado(u.beneficio_total), eurFirmado(u.realizado) + " realizado · " + eurFirmado(u.latente) + " latente", clase(u.beneficio_total)],
      ["Operaciones", cerradas.length + " cerradas", aciertos + " en positivo · " + abiertas.length + " jugadores en plantilla", ""]
    ].map(function(b){
      return '<div class="baldosa"><div class="rotulo">' + b[0] + '</div>' +
        '<div class="valor num ' + b[3] + '">' + b[1] + '</div><div class="pie">' + b[2] + '</div></div>';
    }).join("");

    var filas, cab;
    if (vista === "cerradas"){
      filas = cerradas.slice().sort(function(a,b){ return b.p - a.p; });
      cab = ["Jugador","Entrada","Pagó","Salida","Cobró","Resultado"];
    } else {
      filas = abiertas.slice().sort(function(a,b){ return b.p - a.p; });
      cab = ["Jugador","Entrada","Pagó","","Vale hoy","Latente"];
    }
    if (!filas.length){
      document.getElementById("tabla-detalle").innerHTML = '<p class="vacio">Sin operaciones que mostrar.</p>';
      return;
    }
    document.getElementById("tabla-detalle").innerHTML =
      '<table><thead><tr>' + cab.map(function(c,i){
        return '<th' + (i > 1 ? ' class="der"' : '') + '>' + c + '</th>'; }).join("") +
      '</tr></thead><tbody>' + filas.map(function(t){
        var salida = vista === "cerradas"
          ? '<td class="der"><span class="via">' + esc(t.eout) + '</span> ' + esc(t.dout) + '</td>'
          : '<td class="der"></td>';
        return '<tr><td class="jugador">' + esc(t.j) + '</td>' +
          '<td><span class="via">' + esc(t.ein) + '</span> ' + esc(t.din || "") + '</td>' +
          '<td class="der num">' + eur(t.c) + '</td>' + salida +
          '<td class="der num">' + eur(t.v) + '</td>' +
          '<td class="der num ' + clase(t.p) + '" style="font-weight:600">' + eurFirmado(t.p) + '</td></tr>';
      }).join("") + '</tbody></table>';
  }

  function elegirEquipo(id, mover){
    sel = id;
    document.querySelectorAll("#clasificacion tr[data-id]").forEach(function(x){
      x.setAttribute("aria-selected", Number(x.dataset.id) === sel);
    });
    pintarDetalle();
    pintarGrafica();
    if (mover) document.getElementById("s-detalle").scrollIntoView({behavior:"smooth", block:"start"});
  }
  document.getElementById("clasificacion").addEventListener("click", function(e){
    var th = e.target.closest("[data-orden]");
    if (th){
      var k = th.dataset.orden;
      ordenAsc = k === ordenPor ? !ordenAsc : false;
      ordenPor = k;
      return pintarClasificacion();
    }
    var tr = e.target.closest("tr[data-id]");
    if (tr) elegirEquipo(Number(tr.dataset.id), true);
  });
  document.getElementById("clasificacion").addEventListener("keydown", function(e){
    if (e.key !== "Enter" && e.key !== " ") return;
    var tr = e.target.closest("tr[data-id]");
    if (tr){ e.preventDefault(); elegirEquipo(Number(tr.dataset.id), true); }
  });
  function cambiarVista(v){
    vista = v;
    document.getElementById("btn-cerradas").setAttribute("aria-pressed", v === "cerradas");
    document.getElementById("btn-abiertas").setAttribute("aria-pressed", v === "abiertas");
    pintarDetalle();
  }
  document.getElementById("btn-cerradas").onclick = function(){ cambiarVista("cerradas"); };
  document.getElementById("btn-abiertas").onclick = function(){ cambiarVista("abiertas"); };
  pintarDetalle();

  // Próxima jornada
  var AL = D.alineaciones, filtroJor = "mios";
  function pintarJornada(){
    var cont = document.getElementById("jor-partidos"), res = document.getElementById("jor-resumen");
    if (!AL || !AL.partidos || !AL.partidos.length){
      document.getElementById("jor-filtro").style.display = "none";
      res.innerHTML = "";
      cont.innerHTML = '<div class="marco"><p class="vacio">Todavía no hay onces probables publicados ' +
        'para la próxima jornada.</p></div>';
      return;
    }
    document.getElementById("jor-titulo").textContent = "Jornada " + AL.jornada;

    var mios = [];
    AL.partidos.forEach(function(p){
      ["once_local","once_visitante","banquillo"].forEach(function(g){
        p[g].forEach(function(j){
          if (j.dueno === D.yo) mios.push({j:j, p:p, campo:g !== "banquillo"});
        });
      });
    });
    mios.sort(function(a,b){ return b.j.probabilidad - a.j.probabilidad; });
    var enOnce = mios.filter(function(m){ return m.campo; }).length;
    res.innerHTML = '<div class="jor-resumen"><div class="rotulo">Tus jugadores</div>' +
      '<div style="font-size:14px;margin-top:4px">' + enOnce + ' de tus ' + mios.length +
      ' jugadores aparecen en un once probable.</div><ul>' + mios.map(function(m){
        return '<li><span>' + esc(m.j.nombre) + '</span><span class="num ' +
          (m.campo ? "pos" : "") + '">' + (m.campo ? "once" : "banquillo") + '</span></li>';
      }).join("") + '</ul></div>';

    cont.innerHTML = AL.partidos.map(function(p){
      function campo(lista, equipo){
        var piezas = lista.map(function(j){
          var suyo = j.dueno === D.yo, deLaLiga = j.dueno != null;
          if (filtroJor === "mios" && !suyo) return "";
          if (filtroJor === "liga" && !deLaLiga) return "";
          var marca = j.etiqueta && !/%/.test(j.etiqueta) ? (j.titular ? "XI" : "S")
                                                         : j.probabilidad + "%";
          return '<div class="pieza ' + (suyo ? "mio" : deLaLiga ? "rival" : "libre") +
            '" style="left:' + j.x + '%;top:' + j.y + '%" title="' + esc(j.nombre) +
            (deLaLiga ? " — " + esc(j.dueno_nombre) : " — sin dueño") + '">' +
            '<span class="ficha-jug">' + marca + '</span>' +
            '<span class="etq">' + esc(j.nombre) + '</span>' +
            (deLaLiga ? '<span class="quien">' + esc(j.dueno_nombre) + '</span>' : '') + '</div>';
        }).join("");
        return '<div><div class="jor-meta" style="margin-bottom:5px">' + esc(equipo) + '</div>' +
          '<div class="campo"><span class="raya medio"></span><span class="raya circulo"></span>' +
          '<span class="raya area"></span>' + piezas + '</div></div>';
      }
      var f = new Date(p.fecha);
      var cuando = f.toLocaleDateString("es-ES", {weekday:"short", day:"numeric", month:"short"}) +
        " · " + f.toLocaleTimeString("es-ES", {hour:"2-digit", minute:"2-digit"});
      return '<div class="jor-partido"><div class="jor-cab">' +
        '<span class="jor-equipos">' + esc(p.local) + " – " + esc(p.visitante) + '</span>' +
        '<span class="jor-meta">' + cuando +
        (p.confirmado ? ' <span class="insignia">once definitivo</span>' : '') + '</span></div>' +
        '<div class="campos">' + campo(p.once_local, p.local) + campo(p.once_visitante, p.visitante) +
        '</div></div>';
    }).join("");
  }
  document.getElementById("jor-filtro").addEventListener("click", function(e){
    var b = e.target.closest("[data-jor]");
    if (!b) return;
    filtroJor = b.dataset.jor;
    this.querySelectorAll("[data-jor]").forEach(function(x){
      x.setAttribute("aria-pressed", x.dataset.jor === filtroJor); });
    pintarJornada();
  });
  pintarJornada();

  // Evolución del patrimonio
  var FECHAS = D.evolucion.fechas, SERIES = D.evolucion.series;
  // Ocho tonos validados para daltonismo. A partir del noveno equipo se reutiliza el tono
  // pero con trazo discontinuo, para que la identidad nunca dependa solo del color.
  var PAL = ["--serie-1","--serie-2","--serie-3","--serie-4","--serie-5","--serie-6","--serie-7","--serie-8"];
  var orden = U.map(function(u){ return u.id; }).slice().sort(function(a,b){ return a - b; });
  function estilo(id){
    var i = orden.indexOf(id);
    return {color:"var(" + PAL[i % 8] + ")", guion:i >= 8 ? "6 4" : null};
  }
  var visibles = {};
  U.slice(0, 4).forEach(function(u){ visibles[u.id] = true; });
  visibles[D.yo] = true;

  var lienzo = document.getElementById("ev-lienzo");
  function muestra(id){
    var e = estilo(id);
    return '<svg width="16" height="8" aria-hidden="true"><line x1="0" y1="4" x2="16" y2="4" ' +
      'stroke="' + e.color + '" stroke-width="2.5" stroke-linecap="round"' +
      (e.guion ? ' stroke-dasharray="' + e.guion + '"' : '') + '/></svg>';
  }
  document.getElementById("ev-fichas").innerHTML = U.map(function(u){
    return '<button type="button" class="ficha" data-ev="' + u.id + '" aria-pressed="' +
      !!visibles[u.id] + '">' + muestra(u.id) + esc(u.nombre) + '</button>';
  }).join("");

  var W = 940, Hg = 330, m = {t:16, r:18, b:30, l:70}, ejeX = [], escalaY = null;
  function pintarGrafica(){
    var activos = U.filter(function(u){ return visibles[u.id]; });
    if (!activos.length){
      lienzo.innerHTML = '<p class="vacio">Elige al menos un equipo para dibujar la gráfica.</p>';
      return;
    }
    var vals = [];
    activos.forEach(function(u){ (SERIES[u.id] || []).forEach(function(v){ if (v !== null) vals.push(v); }); });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var pad = (hi - lo) * .10 || 1e6; lo -= pad; hi += pad;
    var X = function(i){ return m.l + i * (W - m.l - m.r) / Math.max(1, FECHAS.length - 1); };
    var Y = function(v){ return m.t + (hi - v) / (hi - lo) * (Hg - m.t - m.b); };
    ejeX = FECHAS.map(function(_, i){ return X(i); });
    escalaY = Y;

    var s = '<svg class="grafico" viewBox="0 0 ' + W + ' ' + Hg + '" role="img" aria-label="' +
      'Patrimonio diario de ' + activos.length + ' equipos desde el 1 de agosto">';
    [0,.25,.5,.75,1].forEach(function(t){
      var v = lo + t * (hi - lo), y = Y(v).toFixed(1);
      s += '<line x1="' + m.l + '" x2="' + (W-m.r) + '" y1="' + y + '" y2="' + y +
        '" stroke="var(--linea)" stroke-width="1"/>' +
        '<text x="' + (m.l-10) + '" y="' + (Y(v)+4).toFixed(1) + '" text-anchor="end" font-size="11.5" ' +
        'fill="var(--tinta-3)" font-family="var(--sans)">' + millones(v) + '</text>';
    });
    var paso = Math.ceil(FECHAS.length / 7);
    FECHAS.forEach(function(f, i){
      if (i % paso && i !== FECHAS.length - 1) return;
      s += '<text x="' + X(i).toFixed(1) + '" y="' + (Hg-8) + '" text-anchor="middle" font-size="11.5" ' +
        'fill="var(--tinta-3)" font-family="var(--sans)">' + f.slice(8) + "/" + f.slice(5,7) + '</text>';
    });
    activos.forEach(function(u){
      var e = estilo(u.id), pts = SERIES[u.id] || [], d = "", abierto = false;
      pts.forEach(function(v, i){
        if (v === null){ abierto = false; return; }
        d += (abierto ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1) + " ";
        abierto = true;
      });
      s += '<path d="' + d.trim() + '" fill="none" stroke="' + e.color + '" stroke-width="2" ' +
        'stroke-linejoin="round" stroke-linecap="round"' +
        (e.guion ? ' stroke-dasharray="' + e.guion + '"' : '') + '/>';
    });
    s += '<line id="ev-cursor" y1="' + m.t + '" y2="' + (Hg-m.b) + '" stroke="var(--eje)" ' +
      'stroke-width="1" style="display:none"/>';
    lienzo.innerHTML = s + '</svg><div class="globo" id="ev-globo" style="display:none"></div>';
  }

  function alPasar(ev){
    var svg = lienzo.querySelector("svg"), globo = document.getElementById("ev-globo");
    if (!svg || !globo) return;
    var caja = svg.getBoundingClientRect(), escala = W / caja.width;
    var x = (ev.clientX - caja.left) * escala;
    var i = 0, mejor = Infinity;
    ejeX.forEach(function(px, k){ var dd = Math.abs(px - x); if (dd < mejor){ mejor = dd; i = k; } });
    var cursor = document.getElementById("ev-cursor");
    cursor.setAttribute("x1", ejeX[i]); cursor.setAttribute("x2", ejeX[i]);
    cursor.style.display = "";

    var activos = U.filter(function(u){ return visibles[u.id] && (SERIES[u.id] || [])[i] !== null &&
      (SERIES[u.id] || [])[i] !== undefined; });
    activos.sort(function(a,b){ return SERIES[b.id][i] - SERIES[a.id][i]; });
    globo.innerHTML = '<b>' + FECHAS[i].split("-").reverse().join("/") + '</b>' + activos.map(function(u){
      return '<div><span>' + muestra(u.id) + esc(u.nombre) + '</span>' +
        '<span class="num">' + millones(SERIES[u.id][i]) + '</span></div>';
    }).join("");
    globo.style.display = "";
    var izq = ejeX[i] / escala, aFuera = izq + 190 > caja.width;
    globo.style.left = Math.max(4, aFuera ? izq - globo.offsetWidth - 12 : izq + 12) + "px";
    globo.style.top = "6px";
  }
  lienzo.addEventListener("mousemove", alPasar);
  lienzo.addEventListener("mouseleave", function(){
    var c = document.getElementById("ev-cursor"), g = document.getElementById("ev-globo");
    if (c) c.style.display = "none";
    if (g) g.style.display = "none";
  });

  document.getElementById("ev-fichas").addEventListener("click", function(e){
    var b = e.target.closest("[data-ev]");
    if (!b) return;
    var id = Number(b.dataset.ev);
    visibles[id] = !visibles[id];
    b.setAttribute("aria-pressed", !!visibles[id]);
    pintarGrafica();
  });
  function fijarVisibles(fn){
    U.forEach(function(u, i){ visibles[u.id] = fn(u, i); });
    document.querySelectorAll("[data-ev]").forEach(function(b){
      b.setAttribute("aria-pressed", !!visibles[Number(b.dataset.ev)]);
    });
    pintarGrafica();
  }
  document.getElementById("ev-todos").onclick = function(){ fijarVisibles(function(){ return true; }); };
  document.getElementById("ev-ninguno").onclick = function(){ fijarVisibles(function(){ return false; }); };
  document.getElementById("ev-podio").onclick = function(){ fijarVisibles(function(u, i){ return i < 4; }); };
  pintarGrafica();

  // Tema
  document.getElementById("tema").onclick = function(){
    var oscuro = document.documentElement.getAttribute("data-theme") === "dark" ||
      (!document.documentElement.hasAttribute("data-theme") &&
       matchMedia("(prefers-color-scheme: dark)").matches);
    document.documentElement.setAttribute("data-theme", oscuro ? "light" : "dark");
  };
})();
</script>
"""


if __name__ == "__main__":
    print("escrito:", build())
