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

    payload = {
        "liga": liga["liga"], "actualizado": liga["actualizado"], "yo": liga["usuario_propio"],
        "usuarios": liga["usuarios"], "cerradas": cerradas, "abiertas": abiertas,
        "historico": hist,
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
  --acento:#2a78d6; --serie-1:#2a78d6; --serie-2:#eb6834;
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
  --acento:#3987e5; --serie-1:#3987e5; --serie-2:#d95926;
  --sube:#2cb72c; --baja:#e66767; --sube-f:rgba(44,183,44,.16); --baja-f:rgba(230,103,103,.16);
  color-scheme:dark;
}}
:root[data-theme="dark"]{
  --plano:#0c0e0d; --tarjeta:#1a1a19; --hueco:#232523;
  --tinta:#f4f5f3; --tinta-2:#c3c2b7; --tinta-3:#898781;
  --linea:#2c2c2a; --borde:rgba(255,255,255,.10); --eje:#383835;
  --acento:#3987e5; --serie-1:#3987e5; --serie-2:#d95926;
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
button[aria-pressed="true"]{background:var(--tinta);color:var(--plano);border-color:var(--tinta)}

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
.fila[aria-pressed="true"]{background:var(--hueco);box-shadow:inset 3px 0 0 var(--acento)}
.cabecera-tabla{display:grid;grid-template-columns:30px minmax(120px,1.35fr) minmax(150px,1.5fr) 108px 108px 96px;
  gap:12px;padding:9px 16px;background:var(--hueco);border-bottom:1px solid var(--linea)}
.puesto{font-family:var(--titular);font-size:17px;color:var(--tinta-3);font-weight:600}
.equipo{font-family:var(--titular);font-size:17px;font-weight:600;line-height:1.15;overflow-wrap:anywhere}
.tuyo{display:inline-block;background:var(--acento);color:#fff;border-radius:4px;
  font-family:var(--sans);font-size:10px;font-weight:600;padding:1px 5px;margin-left:6px;vertical-align:2px;letter-spacing:.04em}
.der{text-align:right}
.barra{height:9px;border-radius:3px 4px 4px 3px;background:var(--acento);min-width:3px}
.pista{background:var(--hueco);border-radius:4px;height:9px;overflow:hidden}
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
        <button type="button" id="btn-cerradas" aria-pressed="true">Operaciones cerradas</button>
        <button type="button" id="btn-abiertas" aria-pressed="false">Plantilla actual</button>
      </div>
    </div>
    <div class="rejilla-detalle" id="baldosas"></div>
    <div class="envoltura-tabla"><div id="tabla-detalle"></div></div>
  </section>

  <section id="s-evolucion">
    <div class="encabezado-seccion">
      <h2>Evolución del patrimonio</h2>
      <p class="nota" id="nota-evolucion"></p>
    </div>
    <div class="marco" id="marco-evolucion"></div>
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
      '<span class="equipo">' + esc(u.nombre) + (u.id === D.yo ? '<span class="tuyo">TÚ</span>' : '') + '</span>' +
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

  // Evolución
  var H = D.historico;
  var marco = document.getElementById("marco-evolucion");
  if (H.length < 2){
    document.getElementById("nota-evolucion").textContent =
      "El histórico se llena con cada actualización diaria.";
    marco.innerHTML = '<p class="vacio">Solo hay una foto guardada, la del ' +
      H[0].fecha.split("-").reverse().join("/") + '. Mañana habrá línea.</p>';
  } else {
    document.getElementById("nota-evolucion").textContent =
      "Cada línea es un equipo; la resaltada es el que tengas seleccionado arriba.";
    var W = 900, Hg = 300, m = {t:14, r:16, b:26, l:64};
    var series = U.map(function(u){
      return {id:u.id, nombre:u.nombre, pts:H.map(function(d){
        var x = d.usuarios.filter(function(z){ return z.id === u.id; })[0];
        return x ? x.patrimonio : null; })};
    });
    var todos = [].concat.apply([], series.map(function(s){ return s.pts; })).filter(function(v){ return v !== null; });
    var lo = Math.min.apply(null, todos), hi = Math.max.apply(null, todos);
    var pad = (hi - lo) * .08 || 1e6; lo -= pad; hi += pad;
    var X = function(i){ return m.l + i * (W - m.l - m.r) / Math.max(1, H.length - 1); };
    var Y = function(v){ return m.t + (hi - v) / (hi - lo) * (Hg - m.t - m.b); };
    var ticks = [0,.25,.5,.75,1].map(function(t){ return lo + t * (hi - lo); });
    var svg = '<svg class="grafico" viewBox="0 0 ' + W + ' ' + Hg + '" role="img" ' +
      'aria-label="Evolución del patrimonio de cada equipo">';
    ticks.forEach(function(v){
      svg += '<line x1="' + m.l + '" x2="' + (W-m.r) + '" y1="' + Y(v).toFixed(1) + '" y2="' + Y(v).toFixed(1) +
        '" stroke="var(--linea)" stroke-width="1"/>' +
        '<text x="' + (m.l-9) + '" y="' + (Y(v)+4).toFixed(1) + '" text-anchor="end" font-size="11" ' +
        'fill="var(--tinta-3)" font-family="var(--sans)">' + millones(v) + '</text>';
    });
    series.forEach(function(s){
      var d = s.pts.map(function(v,i){ return (i ? "L" : "M") + X(i).toFixed(1) + " " + Y(v).toFixed(1); }).join(" ");
      svg += '<path d="' + d + '" fill="none" stroke="' + (s.id === sel ? "var(--acento)" : "var(--eje)") +
        '" stroke-width="' + (s.id === sel ? 2.5 : 1.2) + '" stroke-linejoin="round" stroke-linecap="round"/>';
    });
    H.forEach(function(d,i){
      svg += '<text x="' + X(i).toFixed(1) + '" y="' + (Hg-7) + '" text-anchor="middle" font-size="11" ' +
        'fill="var(--tinta-3)" font-family="var(--sans)">' + d.fecha.slice(8) + "/" + d.fecha.slice(5,7) + '</text>';
    });
    marco.innerHTML = svg + '</svg>';
  }

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
