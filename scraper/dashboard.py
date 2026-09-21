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

    payload = {
        "liga": liga["liga"], "actualizado": liga["actualizado"], "yo": liga["usuario_propio"],
        "usuarios": liga["usuarios"], "cerradas": cerradas, "abiertas": abiertas,
        "evolucion": {"fechas": fechas, "series": series},
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
.fila{display:grid;grid-template-columns:30px minmax(120px,1.35fr) minmax(150px,1.5fr) 108px 108px 96px;
  gap:12px;align-items:center;padding:11px 16px;border-top:1px solid var(--linea);
  width:100%;background:none;border-left:0;border-right:0;border-bottom:0;text-align:left;cursor:pointer;color:inherit;font-size:14px}
.fila:first-of-type{border-top:0}
.fila:hover{background:var(--hueco)}
.fila[aria-pressed="true"]{background:var(--hueco);color:var(--tinta);box-shadow:inset 3px 0 0 var(--acento)}
.cabecera-tabla{display:grid;grid-template-columns:30px minmax(120px,1.35fr) minmax(150px,1.5fr) 108px 108px 96px;
  gap:12px;padding:9px 16px;background:var(--hueco);border-bottom:1px solid var(--linea)}
.puesto{font-family:var(--titular);font-size:17px;color:var(--tinta-3);font-weight:600}
.equipo{font-family:var(--titular);font-size:17px;font-weight:600;line-height:1.15;overflow-wrap:anywhere}
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
.filas-div{display:grid;gap:9px}
.fila-div{display:grid;grid-template-columns:minmax(96px,150px) 1fr;gap:12px;align-items:center;font-size:13px}
.pista-div{position:relative;height:26px}
.cero{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--eje)}
.marca{position:absolute;height:9px;border-radius:2px}
.marca.r{top:1px;background:var(--serie-1)}
.marca.l{top:15px;background:var(--serie-2)}

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
  .fila,.cabecera-tabla{grid-template-columns:26px 1fr 96px;gap:10px}
  .ocultar-movil{display:none}
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
      <h2>Clasificación por patrimonio</h2>
      <p class="nota">Patrimonio = saldo en caja + valor de la plantilla. Pulsa un equipo para ver sus operaciones.</p>
    </div>
    <div class="tabla">
      <div class="cabecera-tabla rotulo">
        <span>#</span><span>Equipo</span><span class="ocultar-movil">Patrimonio</span>
        <span class="der ocultar-movil">Saldo</span><span class="der ocultar-movil">Plantilla</span><span class="der">Total</span>
      </div>
      <div id="clasificacion"></div>
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
      <p class="nota">Lo ya embolsado al vender frente a lo que se ganaría vendiendo hoy la plantilla.</p>
    </div>
    <div class="marco">
      <div class="leyenda">
        <span class="llave"><span class="muestra" style="background:var(--serie-1)"></span>Realizado, ventas ya cerradas</span>
        <span class="llave"><span class="muestra" style="background:var(--serie-2)"></span>Latente, plantilla actual</span>
      </div>
      <div class="filas-div" id="divergente"></div>
    </div>
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

  // Clasificación
  var maxPat = Math.max.apply(null, U.map(function(u){ return u.patrimonio; }));
  document.getElementById("clasificacion").innerHTML = U.map(function(u, i){
    var ancho = Math.max(2, u.patrimonio / maxPat * 100);
    return '<button class="fila" type="button" data-id="' + u.id + '" aria-pressed="' + (u.id === sel) + '">' +
      '<span class="puesto num">' + (i + 1) + '</span>' +
      '<span class="equipo">' + esc(u.nombre) + '</span>' +
      '<span class="pista ocultar-movil"><span class="barra" style="width:' + ancho.toFixed(1) + '%"></span></span>' +
      '<span class="der num ocultar-movil ' + clase(u.saldo) + '">' + eur(u.saldo) + '</span>' +
      '<span class="der num ocultar-movil">' + eur(u.valor_equipo) + '</span>' +
      '<span class="der num" style="font-weight:600">' + millones(u.patrimonio) + '</span>' +
    '</button>';
  }).join("");
  var enRojo = U.filter(function(u){ return u.saldo < 0; }).length;
  document.getElementById("pie-clasificacion").textContent =
    U.length + " equipos · " + enRojo + " con el saldo en números rojos · " +
    "diferencia entre el primero y el último: " + eur(U[0].patrimonio - U[U.length-1].patrimonio);

  // Realizado vs latente
  var tope = Math.max.apply(null, U.map(function(u){
    return Math.max(Math.abs(u.realizado), Math.abs(u.latente)); }));
  var porBeneficio = U.slice().sort(function(a,b){ return b.beneficio_total - a.beneficio_total; });
  document.getElementById("divergente").innerHTML = porBeneficio.map(function(u){
    function marca(v, cls){
      var ancho = Math.abs(v) / tope * 50;
      var izq = v >= 0 ? 50 : 50 - ancho;
      return '<span class="marca ' + cls + '" style="left:' + izq.toFixed(2) + '%;width:' +
        Math.max(0.4, ancho).toFixed(2) + '%"></span>';
    }
    return '<div class="fila-div">' +
      '<span style="overflow-wrap:anywhere">' + esc(u.nombre) + '</span>' +
      '<span class="pista-div" title="' + esc(u.nombre) + ' — realizado ' + eurFirmado(u.realizado) +
        ', latente ' + eurFirmado(u.latente) + '">' +
        '<span class="cero" style="left:50%"></span>' + marca(u.realizado, "r") + marca(u.latente, "l") +
      '</span></div>';
  }).join("");

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

  document.getElementById("clasificacion").addEventListener("click", function(e){
    var b = e.target.closest("[data-id]");
    if (!b) return;
    sel = Number(b.dataset.id);
    this.querySelectorAll(".fila").forEach(function(x){
      x.setAttribute("aria-pressed", Number(x.dataset.id) === sel);
    });
    pintarDetalle();
    document.getElementById("s-detalle").scrollIntoView({behavior:"smooth", block:"start"});
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
