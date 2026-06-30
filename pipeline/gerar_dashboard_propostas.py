#!/usr/bin/env python3
"""Gera o dashboard HTML de PROPOSTAS de custeio MAC/PAP a partir de /tmp/propostas_dataset.json"""
import json
from datetime import datetime
from pathlib import Path

BUILD = datetime.now().strftime("%Y-%m-%d %H:%M")

_ds = Path("/tmp/propostas_dataset.json")
if not _ds.exists():
    _ds = Path.home() / "raiox/cache/propostas_dataset.json"  # backup permanente
DS = json.loads(_ds.read_text())
muns = DS.get("muns") or DS.get("municipios")
ANOS = DS["anos"]
ANO_DRILL = DS["ano_drill"]

# garante campo faf
for m in muns:
    m.setdefault("faf", {"saldo": 0.0, "years": {}})

# número único = propostas paradas + desconto FAF + saldo parado (ano de referência)
def numero_unico(m, ano=ANO_DRILL):
    a = m["anos"].get(str(ano), {})
    gap = a.get("mac", {}).get("recuperar", 0) + a.get("pap", {}).get("recuperar", 0)
    desc = m["faf"]["years"].get(str(ano), {}).get("desc", 0)
    return gap + desc + m["faf"].get("saldo", 0)

muns_sorted = sorted(muns, key=numero_unico, reverse=True)

payload = {"anos": ANOS, "ano_drill": ANO_DRILL, "gerado_em": DS.get("gerado_em"),
           "ufs": DS.get("ufs"), "muns": muns_sorted, "build": BUILD}

HTML = r"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"><meta http-equiv="Pragma" content="no-cache"><meta http-equiv="Expires" content="0">
<title>Raio-X de Captação SUS — Propostas MAC/PAP × Desconto FAF · G3</title>
__CHARTJS__
__JSPDF__
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Arial,Helvetica,sans-serif;background:#d6dde5;color:#1f2933;font-size:13px}
.hdr{background:linear-gradient(90deg,#0b3349,#15506f);color:#fff;padding:18px 26px;display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:50;box-shadow:0 2px 8px rgba(11,51,73,.25)}
.hdr h1{font-size:25px;font-weight:800;letter-spacing:-.4px}
.hdr .sub{font-size:12px;opacity:.85;margin-top:4px}
.tabs{display:flex;gap:2px;background:#0e3d59;padding:0 22px}
.tab{padding:9px 18px;color:#cdd9e3;cursor:pointer;font-size:12px;font-weight:600;border-bottom:3px solid transparent}
.tab.on{color:#fff;border-bottom-color:#48c9b0;background:rgba(255,255,255,.06)}
.view{display:none;padding:18px 22px}
.view.on{display:block}
/* ---- overview ---- */
.toolbar{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.toolbar select,.toolbar input{padding:7px 9px;border:1px solid #c3ccd6;border-radius:6px;font-size:12px;background:#fff}
.toolbar input{flex:1;min-width:180px}
.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}
.scard{background:#fff;border-radius:9px;padding:13px 15px;border:1px solid #e1e6ec}
.scard .l{font-size:10px;text-transform:uppercase;letter-spacing:.4px;color:#8a97a5}
.scard .v{font-size:19px;font-weight:700;margin-top:4px}
.scard .sc-sub{font-size:9.5px;color:#aab4bf;margin-top:3px}
.scard.sol .v{color:#ca6f1e}.scard.apr .v{color:#1e8449}.scard.rec .v{color:#b9770e}.scard.apr2 .v{color:#c0392b}.scard.pct .v{color:#7d3c98}
.scard.num{background:linear-gradient(120deg,#f7f2fb,#efe3f7);border-color:#d7bfe8}.scard.num .v{color:#7d3c98;font-size:21px}
table.gtbl{width:100%;border-collapse:collapse;background:#fff;border-radius:9px;overflow:hidden;border:1px solid #e1e6ec}
table.gtbl th{background:#f4f6f9;padding:9px 10px;text-align:left;font-size:10px;text-transform:uppercase;letter-spacing:.3px;color:#7a8794;cursor:pointer;white-space:nowrap}
table.gtbl th.num,table.gtbl td.num{text-align:right}
table.gtbl td{padding:8px 10px;border-top:1px solid #eef1f5;font-size:12px}
table.gtbl tr.mrow{cursor:pointer}
table.gtbl tr.mrow:hover{background:#f0f7fb}
.bar-mini{height:6px;border-radius:3px;background:#eef1f5;overflow:hidden;margin-top:3px}
.bar-mini>i{display:block;height:100%}
.pill{display:inline-block;padding:2px 8px;border-radius:11px;font-size:10px;font-weight:700}
.p-apr{background:#d4efdf;color:#1e8449}.p-an{background:#fdebd0;color:#ca6f1e}.p-pend{background:#fadbd8;color:#c0392b}.p-par{background:#d6eaf8;color:#2471a3}
/* ---- detail ---- */
.back{background:none;border:none;color:#1a5276;cursor:pointer;font-size:12px;font-weight:600;margin-bottom:8px}
.dhead{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}
.dhead .nm{font-size:23px;font-weight:700;color:#0e3d59}
.dhead .meta{font-size:12px;color:#8a97a5;margin-top:2px}
.btn{padding:8px 14px;border:none;border-radius:7px;cursor:pointer;font-size:12px;font-weight:600}
.btn-pdf{background:#c0392b;color:#fff}.btn-x{background:#1e8449;color:#fff;margin-left:6px}.btn-live{background:#2471a3;color:#fff;margin-left:6px;text-decoration:none;display:inline-block}
.btn-wa{background:#25D366;color:#fff}
.btn-signal{background:#3A76F0;color:#fff}
.blocos{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.bloco{background:#fff;border-radius:10px;border:1px solid #e1e6ec;padding:14px 16px}
.bloco h3{font-size:13px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.tag{font-size:10px;padding:2px 8px;border-radius:5px;font-weight:700}
.tag.mac{background:#d6eaf8;color:#1a5276}.tag.pap{background:#d4efdf;color:#1e8449}
.k3{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-bottom:10px}
.k3 .kk{background:#f8fafb;border-radius:7px;padding:8px 10px;text-align:center}
.k3 .kk .l{font-size:9px;text-transform:uppercase;color:#8a97a5;letter-spacing:.3px}
.k3 .kk .v{font-size:15px;font-weight:700;margin-top:2px}
.kk.s .v{color:#1a5276}.kk.a .v{color:#1e8449}.kk.r .v{color:#ca6f1e}
.row2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}
.panel{background:#fff;border-radius:10px;border:1px solid #e1e6ec;padding:14px 16px}
.panel h3{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#6b7785;margin-bottom:10px}
.chart-wrap{position:relative;height:210px}
.diag{background:linear-gradient(120deg,#fff,#fbf6ee);border-left:4px solid #ca6f1e}
.diag .big{font-size:26px;font-weight:800;color:#ca6f1e;margin:4px 0}
.diag .rec{font-size:14px;color:#1e8449;font-weight:700}
.hero{display:grid;grid-template-columns:1.1fr 1fr;gap:0;background:linear-gradient(120deg,#5b2c83,#7d3c98);color:#fff;border-radius:12px;overflow:hidden;margin-bottom:14px}
.hero-l{padding:18px 22px}
.hero-l .hl{font-size:11px;text-transform:uppercase;letter-spacing:.5px;opacity:.85}
.hero-l .hbig{font-size:34px;font-weight:800;margin:4px 0;letter-spacing:-.5px}
.hero-l .hsub{font-size:12px;opacity:.95}
.hero-r{background:rgba(0,0,0,.12);padding:14px 20px;display:flex;flex-direction:column;justify-content:center;gap:8px}
.hcomp{display:flex;justify-content:space-between;align-items:center;font-size:12px;border-bottom:1px solid rgba(255,255,255,.12);padding-bottom:6px}
.hcomp:last-child{border-bottom:none}
.hcl{opacity:.9}.hcv{font-weight:700}
.calc-grid{display:grid;grid-template-columns:1fr auto auto auto;font-size:11.5px;border:1px solid #e1e6ec;border-radius:7px;overflow:hidden}
.cgh{background:#f4f6f9;padding:7px 11px;font-size:10px;text-transform:uppercase;color:#8a97a5;font-weight:700;border-bottom:1px solid #e1e6ec}
.cgc{padding:8px 11px;border-bottom:1px solid #f0f3f6}
.cgc.r{text-align:right}.cgc.rc{color:#1e8449}.cgc.pd{color:#c0392b}
.cgc.tr{font-weight:800;background:#f7f2fb;color:#5b2c83}.cgc.tr.rc{color:#1e8449}.cgc.tr.pd{color:#c0392b}
.propt{width:100%;border-collapse:collapse;font-size:11px}
.propt th{background:#f4f6f9;padding:6px 8px;text-align:left;font-size:9px;text-transform:uppercase;color:#7a8794}
.propt th.num{text-align:right}
.propt td{padding:6px 8px;border-top:1px solid #eef1f5}
.propt td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.propt a{color:#2471a3;text-decoration:none}
/* ---- methodology ---- */
.propbox{max-width:920px;background:#fff;border:1px solid #d7bfe8;border-left:4px solid #7d3c98;border-radius:10px;padding:16px 20px;margin-bottom:16px}
.propbox-h{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
.propbox-f{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px}
.propbox-f input{padding:8px 10px;border:1px solid #c3ccd6;border-radius:6px;font-size:12px}
.method{max-width:920px;background:#fff;border-radius:10px;border:1px solid #e1e6ec;padding:26px 32px;line-height:1.55}
.method h2{color:#0e3d59;font-size:20px;margin:22px 0 8px}
.method h2:first-child{margin-top:0}
.method h3{color:#1a5276;font-size:15px;margin:16px 0 6px}
.method p{margin:7px 0;color:#3a4754}
.method ul,.method ol{margin:7px 0 7px 22px}
.method li{margin:4px 0}
.method table{width:100%;border-collapse:collapse;margin:10px 0;font-size:12px}
.method th{background:#0e3d59;color:#fff;padding:7px 9px;text-align:left;font-size:11px}
.method td{padding:7px 9px;border-bottom:1px solid #eef1f5;vertical-align:top}
.method blockquote{border-left:3px solid #48c9b0;background:#f3fbf9;padding:9px 14px;margin:10px 0;color:#2c3e50;font-style:italic}
.method code{background:#eef1f5;padding:1px 5px;border-radius:4px;font-size:11px}
.foot{font-size:10px;color:#9aa6b2;margin-top:16px}
.empty{padding:60px;text-align:center;color:#aab4bf}
@media print{.hdr,.tabs,.toolbar,.back,.btn,.btn-pdf,.btn-x,.btn-live,.btn-wa,.btn-signal{display:none!important}.view{padding:0}.panel,.bloco{break-inside:avoid}}
</style></head><body>
<div class="hdr">
  <div><h1>Raio-X de Captação SUS — Propostas MAC/PAP × Desconto FAF</h1>
  <div class="sub" id="hsub"></div></div>
  <div style="text-align:right;font-size:11px;opacity:.85">Fontes: Consulta FNS + Portal FNS<br>G3 Health Service</div>
</div>
<div class="tabs">
  <div class="tab on" data-v="overview" onclick="tab('overview')">Visão geral (ranking)</div>
  <div class="tab" data-v="detail" onclick="tab('detail')">Detalhe do município</div>
  <div class="tab" data-v="method" onclick="tab('method')">Assessoria - Proposta de Trabalho</div>
</div>

<div class="view on" id="v-overview">
  <div class="toolbar">
    <select id="ufSel"><option value="">Todas UFs</option></select>
    <select id="anoSel"></select>
    <select id="ordSel" title="Ordenar por">
      <option value="num">Ordenar: Nº único</option>
      <option value="recup">Ordenar: Recuperável</option>
      <option value="percap">Ordenar: Por habitante</option>
      <option value="rec">Ordenar: Propostas paradas</option>
      <option value="desc">Ordenar: Desconto FAF</option>
      <option value="mun">Ordenar: Nome (A–Z)</option>
    </select>
    <input id="srch" placeholder="Buscar município...">
    <button class="btn btn-wa" onclick="whatsappRanking()" title="Enviar o ranking filtrado no WhatsApp">📱 Enviar ranking</button>
    <span id="cnt" style="font-size:11px;color:#8a97a5"></span>
  </div>
  <div class="summary" id="summary"></div>
  <div id="note" style="font-size:11px;color:#8a97a5;margin:-4px 0 12px"></div>
  <table class="gtbl" id="gtbl">
    <thead><tr>
      <th data-s="mun">Município</th>
      <th class="num" data-s="num">Nº único</th>
      <th class="num" data-s="recup">Recuperável</th>
      <th class="num" data-s="percap">R$/hab</th>
      <th class="num" data-s="rec">Propostas paradas</th>
      <th class="num" data-s="desc">Desconto FAF</th>
    </tr></thead>
    <tbody id="gbody"></tbody>
  </table>
</div>

<div class="view" id="v-detail"><div class="empty" id="detEmpty">Selecione um município na aba <b>Visão geral</b>.</div><div id="detBody" style="display:none"></div></div>

<div class="view" id="v-method">
  <div class="propbox">
    <div class="propbox-h">
      <div><b>Gerar proposta de trabalho (PDF)</b><div style="font-size:11px;color:#6b7785;margin-top:2px">Documento pronto para enviar ao município. Se você selecionar um município na aba <b>Detalhe</b>, os números reais entram na proposta.</div></div>
      <button class="btn btn-pdf" onclick="propostaPDF()">↓ Exportar proposta em PDF</button>
    </div>
    <div class="propbox-f">
      <input id="propMun" placeholder="Município / UF destinatário (ex.: Goiânia/GO)">
      <input id="propSec" placeholder="A/C Secretário(a) de Saúde (opcional)">
      <input id="propResp" placeholder="Responsável G3 (ex.: Gerson Gomes)">
    </div>
  </div>
  <div class="method">__METHOD__</div>
</div>

<script>
const D = __DATA__;
const fmt = v => 'R$ '+(v||0).toLocaleString('pt-BR',{minimumFractionDigits:0,maximumFractionDigits:0});
const fmtK = v => {v=v||0; if(v>=1e9)return 'R$ '+(v/1e9).toFixed(2)+' bi'; if(v>=1e6)return 'R$ '+(v/1e6).toFixed(2)+' mi'; if(v>=1e3)return 'R$ '+(v/1e3).toFixed(0)+' mil'; return fmt(v);};
const pct = (a,b)=> !b?0:Math.round(a/b*100);
const yr = ()=> document.getElementById('anoSel').value;
document.getElementById('hsub').innerHTML = (D.ufs||[]).length+' UFs · '+D.muns.length+' municípios · propostas '+D.anos[0]+'–'+D.anos[D.anos.length-1]+' × desconto FAF · atualizado '+(D.gerado_em||'')+' · <b style="color:#3A76F0">build '+(D.build||'')+' (Signal)</b>';

// year select
const anoSel=document.getElementById('anoSel');
D.anos.slice().reverse().forEach(a=>{const o=document.createElement('option');o.value=a;o.textContent=a;anoSel.appendChild(o);});
anoSel.value=D.ano_drill;
// uf select
[...new Set(D.muns.map(m=>m.uf))].sort().forEach(u=>{const o=document.createElement('option');o.value=u;o.textContent=u;document.getElementById('ufSel').appendChild(o);});

function blocoYr(m,b,a){return (m.anos[a]||{})[b]||{solicitado:0,pago:0,recuperar:0};}
function totYr(m,a){const mac=blocoYr(m,'mac',a),pap=blocoYr(m,'pap',a);return{sol:mac.solicitado+pap.solicitado,apr:mac.pago+pap.pago,rec:mac.recuperar+pap.recuperar};}
function fafYr(m,a){return ((m.faf||{}).years||{})[a]||{desc:0,mac_l:0,pap_l:0,total_l:0};}
function saldo(m){return (m.faf||{}).saldo||0;}
// número único (mesmo exercício): propostas paradas + desconto FAF MAC anual.
// histórico de descontos 2012-22 (saldo) é CONTEXTO acumulado, não entra no headline.
function comps(m,a){const t=totYr(m,a);const d=fafYr(m,a).desc;return{gap:t.rec,desc:d,total:t.rec+d,hist:saldo(m)};}
function numUnico(m,a){return comps(m,a).total;}
// recuperável estimado por componente (conservador)
function recuperavel(c){return c.gap*0.6 + c.desc*0.5;}
// honorário fixo mensal por porte (habitantes) — tabela G3
function investimento(pop){
  pop=pop||0;
  if(pop<=10000) return 2500;
  if(pop<=20000) return 3500;
  if(pop<=30000) return 5000;
  if(pop<=40000) return 6500;
  if(pop<=50000) return 8000;
  if(pop<=100000) return 10000;
  if(pop<=200000) return 12000;
  if(pop<=400000) return 15000;
  if(pop<=500000) return 20000;
  return 25000;
}
function faixaPop(pop){
  pop=pop||0;
  if(pop<=10000) return 'até 10.000 hab';
  if(pop<=20000) return '10.001–20.000 hab';
  if(pop<=30000) return '20.001–30.000 hab';
  if(pop<=40000) return '30.001–40.000 hab';
  if(pop<=50000) return '40.001–50.000 hab';
  if(pop<=100000) return '50.001–100.000 hab';
  if(pop<=200000) return '100.001–200.000 hab';
  if(pop<=400000) return '200.001–400.000 hab';
  if(pop<=500000) return '400.001–500.000 hab';
  return 'acima de 500.000 hab';
}
function perCap(m,a){const p=m.pop||0;return p>0?numUnico(m,a)/p:0;}
const fmtHab = v => v>0?('R$ '+v.toLocaleString('pt-BR',{minimumFractionDigits:0,maximumFractionDigits:0})):'—';

let sortKey='num',sortDir=-1,cur=null;
function filtered(){
  const uf=document.getElementById('ufSel').value,q=document.getElementById('srch').value.toLowerCase().trim(),a=yr();
  let arr=D.muns.filter(m=>(!uf||m.uf===uf)&&(!q||m.mun.toLowerCase().includes(q)));
  arr.sort((x,y)=>{
    let vx,vy;
    if(sortKey==='mun'){vx=x.mun;vy=y.mun;return sortDir*vx.localeCompare(vy);}
    if(sortKey==='num'){vx=numUnico(x,a);vy=numUnico(y,a);return sortDir*(vx-vy);}
    if(sortKey==='recup'){vx=recuperavel(comps(x,a));vy=recuperavel(comps(y,a));return sortDir*(vx-vy);}
    if(sortKey==='percap'){vx=perCap(x,a);vy=perCap(y,a);return sortDir*(vx-vy);}
    if(sortKey==='desc'){vx=fafYr(x,a).desc;vy=fafYr(y,a).desc;return sortDir*(vx-vy);}
    if(sortKey==='sal'){vx=saldo(x);vy=saldo(y);return sortDir*(vx-vy);}
    const tx=totYr(x,a),ty=totYr(y,a);
    if(sortKey==='pct'){vx=pct(tx.apr,tx.sol);vy=pct(ty.apr,ty.sol);}
    else{vx=tx[sortKey];vy=ty[sortKey];}
    return sortDir*(vx-vy);
  });
  return arr;
}
function renderOverview(){
  const a=yr(),arr=filtered();
  document.getElementById('cnt').textContent=arr.length+' municípios';
  let GAP=0,DESC=0,HIST=0;
  arr.forEach(m=>{const c=comps(m,a);GAP+=c.gap;DESC+=c.desc;HIST+=c.hist;});
  const TOT=GAP+DESC;
  document.getElementById('summary').innerHTML=`
    <div class="scard sol"><div class="l">1 · Propostas paradas ${a}</div><div class="v">${fmtK(GAP)}</div><div class="sc-sub">MAC+PAP solicitado e não pago</div></div>
    <div class="scard rec"><div class="l">2 · Desconto FAF MAC ${a}</div><div class="v">${fmtK(DESC)}</div><div class="sc-sub">bruto − líquido retido no ano</div></div>
    <div class="scard num"><div class="l">= Número único ${a}</div><div class="v">${fmtK(TOT)}</div><div class="sc-sub">captação comprometida (1+2)</div></div>
    <div class="scard apr2"><div class="l">Contexto · descontos 2012–22</div><div class="v">${fmtK(HIST)}</div><div class="sc-sub">acumulado histórico (não somado)</div></div>`;
  const atual=(a==String(D.ano_drill));
  document.getElementById('note').innerHTML = (atual
    ? 'Em '+a+' (exercício em andamento) boa parte das "propostas paradas" estão <b>em análise</b> no fluxo normal — acompanhar prazo. Selecione um ano fechado (ex.: '+(D.anos[0])+') para ver o que efetivamente <b>deixou de ser pago</b>. '
    : 'Ano fechado: propostas paradas = MAC+PAP solicitado e não pago. ')
    + 'O <b>número único</b> = propostas paradas + desconto FAF MAC do ano. Os <b>descontos 2012–22</b> são contexto acumulado (recorrência a investigar), não entram no número único.';
  const tb=document.getElementById('gbody');tb.innerHTML='';
  const frag=document.createDocumentFragment();
  arr.slice(0,400).forEach(m=>{
    const c=comps(m,a);const rc=recuperavel(c);const pc=perCap(m,a);
    const tr=document.createElement('tr');tr.className='mrow';tr.onclick=()=>openDetail(m);
    tr.innerHTML=`<td><b>${m.mun}</b> <span style="color:#aab4bf">${m.uf}</span>${m.pop?'<div style="font-size:9.5px;color:#c2cad2">'+m.pop.toLocaleString('pt-BR')+' hab</div>':''}</td>
      <td class="num" style="font-weight:800;color:#7d3c98">${fmtK(c.total)}</td>
      <td class="num" style="color:#1e8449">${fmtK(rc)}</td>
      <td class="num" style="color:#5b2c83">${fmtHab(pc)}</td>
      <td class="num" style="color:#ca6f1e">${fmtK(c.gap)}</td>
      <td class="num" style="color:#b9770e">${fmtK(c.desc)}</td>`;
    frag.appendChild(tr);
  });
  tb.appendChild(frag);
  if(arr.length>400){const tr=document.createElement('tr');tr.innerHTML='<td colspan="6" style="text-align:center;color:#aab4bf">Exibindo 400 de '+arr.length+' (ordenados). Refine a busca para ver mais.</td>';tb.appendChild(tr);}
}
document.querySelectorAll('#gtbl th').forEach(th=>th.onclick=()=>{const k=th.dataset.s;if(sortKey===k)sortDir*=-1;else{sortKey=k;sortDir=k==='mun'?1:-1;}document.getElementById('ordSel').value=['num','recup','percap','rec','desc','mun'].includes(k)?k:'num';renderOverview();});
document.getElementById('ordSel').addEventListener('change',function(){sortKey=this.value;sortDir=this.value==='mun'?1:-1;renderOverview();});
['ufSel','srch','anoSel'].forEach(id=>document.getElementById(id).addEventListener('input',renderOverview));

function tab(v){document.querySelectorAll('.tab').forEach(t=>t.classList.toggle('on',t.dataset.v===v));document.querySelectorAll('.view').forEach(x=>x.classList.remove('on'));document.getElementById('v-'+v).classList.add('on');}

let charts={};
function openDetail(m){
  cur=m;tab('detail');
  const pm=document.getElementById('propMun');if(pm)pm.value=m.mun+'/'+m.uf;
  document.getElementById('detEmpty').style.display='none';
  const db=document.getElementById('detBody');db.style.display='block';
  const a=yr();
  const mac=blocoYr(m,'mac',a),pap=blocoYr(m,'pap',a),t=totYr(m,a);
  const c=comps(m,a), rec=recuperavel(c), perd=c.total-rec;
  const liveBase='https://consultafns.saude.gov.br/#/proposta';
  // maior proposta do município -> abre o detalhe real (dados do fundo municipal)
  const topP=(m.props||[]).slice().sort((x,y)=>y.prop-x.prop)[0];
  const liveHref = topP ? (liveBase+'/'+topP.nu+'/detalhe') : liveBase;
  // props breakdown by status
  const props=(m.props||[]);
  const cnt={APROVADO:0,PARCIAL:0,EM_ANALISE:0};const val={APROVADO:0,PARCIAL:0,EM_ANALISE:0};
  props.forEach(p=>{cnt[p.st]=(cnt[p.st]||0)+1;val[p.st]=(val[p.st]||0)+p.prop;});
  db.innerHTML=`
    <button class="back" onclick="tab('overview')">← voltar ao ranking</button>
    <div class="dhead">
      <div><div class="nm">${m.mun} <span style="font-size:15px;color:#aab4bf">/${m.uf}</span></div>
      <div class="meta">IBGE ${m.ibge} ${m.pop?'· '+m.pop.toLocaleString('pt-BR')+' hab':''} · custeio ${a} · ${props.length} propostas individuais (${ANO})</div></div>
      <div>
        <button class="btn btn-signal" onclick="signalShare()">🔒 Enviar no Signal</button>
        <button class="btn btn-pdf" onclick="pdf()">↓ Diagnóstico PDF</button>
        <button class="btn btn-x" onclick="csv()">↓ Planilha</button>
        <a class="btn btn-live" href="${liveHref}" target="_blank" title="${topP?'Abre a maior proposta do município no Consulta FNS':'Abre o Consulta FNS'}">Abrir no Consulta FNS</a>
      </div>
    </div>
    <div class="hero">
      <div class="hero-l">
        <div class="hl">Captação comprometida em ${a} — número único</div>
        <div class="hbig">${fmt(c.total)}</div>
        <div class="hsub">Recuperável estimado: <b style="color:#aaf0c8">${fmt(rec)}</b> · Risco de perda: <b style="color:#f7c6c6">${fmt(perd)}</b></div>
      </div>
      <div class="hero-r">
        <div class="hcomp"><span class="hcl">1 · Propostas paradas (MAC+PAP)</span><span class="hcv">${fmt(c.gap)}</span></div>
        <div class="hcomp"><span class="hcl">2 · Desconto FAF MAC do ano (bruto−líquido)</span><span class="hcv">${fmt(c.desc)}</span></div>
        <div class="hcomp" style="opacity:.8"><span class="hcl">Contexto: descontos 2012–22 (acumulado)</span><span class="hcv">${fmt(c.hist)}</span></div>
      </div>
    </div>
    <div class="blocos">
      ${blocoCard('MAC','mac',mac)}
      ${blocoCard('PAP','pap',pap)}
    </div>
    <div class="row2">
      <div class="panel"><h3>Solicitado × Recebido por ano</h3><div class="chart-wrap"><canvas id="cYear"></canvas></div></div>
      <div class="panel"><h3>Situação das propostas ${ANO} (nº)</h3><div class="chart-wrap"><canvas id="cStatus"></canvas></div></div>
    </div>
    <div class="panel" style="margin-bottom:14px">
      <h3>Composição do número único — Calculadora G3</h3>
      <div class="calc-grid">
        <div class="cgh">Fonte do "deixou de captar"</div><div class="cgh r">Identificado</div><div class="cgh r" style="color:#1e8449">Recuperável</div><div class="cgh r" style="color:#c0392b">Risco perda</div>
        <div class="cgc">1 · Propostas MAC/PAP paradas (${a})</div><div class="cgc r">${fmt(c.gap)}</div><div class="cgc r rc">${fmt(c.gap*0.6)}</div><div class="cgc r pd">${fmt(c.gap*0.4)}</div>
        <div class="cgc">2 · Desconto FAF MAC do ano (${a})</div><div class="cgc r">${fmt(c.desc)}</div><div class="cgc r rc">${fmt(c.desc*0.5)}</div><div class="cgc r pd">${fmt(c.desc*0.5)}</div>
        <div class="cgc tr">TOTAL — número único</div><div class="cgc r tr">${fmt(c.total)}</div><div class="cgc r rc tr">${fmt(rec)}</div><div class="cgc r pd tr">${fmt(perd)}</div>
        <div class="cgc" style="color:#99a3ad;border-top:2px solid #e1e6ec">Contexto · descontos FAF acumulados 2012–22</div><div class="cgc r" style="color:#99a3ad;border-top:2px solid #e1e6ec">${fmt(c.hist)}</div><div class="cgc" style="color:#99a3ad;border-top:2px solid #e1e6ec;grid-column:span 2;text-align:right;font-style:italic">recorrência a investigar — não somado</div>
      </div>
      <div style="font-size:10px;color:#aab4bf;margin-top:8px">Fontes: Consulta FNS (propostas) + Portal FNS (desconto FAF). Número único = propostas paradas + desconto FAF do ano (mesmo exercício). Os descontos acumulados 2012–22 são mostrados como contexto de recorrência e <b>não</b> entram no total para evitar dupla contagem. Recuperabilidade conservadora e ajustável caso a caso.</div>
    </div>
    <div class="panel">
      <h3>Propostas individuais de custeio — ${ANO}</h3>
      ${props.length? propTable(props):'<div style="color:#aab4bf;padding:10px">Sem propostas individuais de custeio capturadas para '+ANO+'. Consulte a situação atualizada no Consulta FNS.</div>'}
    </div>
    <div class="foot">G3 Health Service Ltda · CNPJ 31.652.744/0001-14 · gerson.gomes@proton.me · +55 61 99255-7690 — Fonte oficial: consultafns.saude.gov.br</div>
  `;
  drawCharts(m);
}
function blocoCard(label,b,d){
  const p=pct(d.pago,d.solicitado);
  const cust=d.cust||{sol:0,pago:0}, incr=d.incr||{sol:0,pago:0};
  return `<div class="bloco"><h3><span class="tag ${b}">${label}</span> Recursos ${label} (custeio + incremento)</h3>
    <div class="k3">
      <div class="kk s"><div class="l">Solicitado</div><div class="v">${fmtK(d.solicitado)}</div></div>
      <div class="kk a"><div class="l">Recebido</div><div class="v">${fmtK(d.pago)}</div></div>
      <div class="kk r"><div class="l">A recuperar</div><div class="v">${fmtK(d.recuperar)}</div></div>
    </div>
    <div style="font-size:11px;color:#6b7785">Aprovação: <b>${p}%</b></div>
    <div class="bar-mini" style="height:8px"><i style="width:${p}%;background:${b==='mac'?'#1a5276':'#1e8449'}"></i></div>
    <table style="width:100%;font-size:10.5px;margin-top:9px;border-collapse:collapse;color:#5a6671">
      <tr style="color:#8a97a5"><td></td><td style="text-align:right">Solicitado</td><td style="text-align:right">Recebido</td><td style="text-align:right">A recuperar</td></tr>
      <tr><td><b>Custeio</b> <span style="color:#aab4bf">(fundo a fundo)</span></td><td style="text-align:right">${fmtK(cust.sol)}</td><td style="text-align:right;color:#1e8449">${fmtK(cust.pago)}</td><td style="text-align:right;color:#ca6f1e">${fmtK(Math.max(0,cust.sol-cust.pago))}</td></tr>
      <tr><td><b>Incremento</b> <span style="color:#aab4bf">(emenda)</span></td><td style="text-align:right">${fmtK(incr.sol)}</td><td style="text-align:right;color:#1e8449">${fmtK(incr.pago)}</td><td style="text-align:right;color:#ca6f1e">${fmtK(Math.max(0,incr.sol-incr.pago))}</td></tr>
    </table>
  </div>`;
}
function propTable(props){
  const lbl={APROVADO:['Aprovado','p-apr'],PARCIAL:['Parcial','p-par'],EM_ANALISE:['Em análise','p-an'],PENDENCIA:['Pendência','p-pend']};
  let rows=props.slice().sort((a,b)=>b.prop-a.prop).map(p=>{
    const L=lbl[p.st]||['?','p-an'];
    return `<tr><td>${p.b.toUpperCase()}</td>
      <td><a href="https://consultafns.saude.gov.br/#/proposta/${p.nu}/detalhe" target="_blank">${p.nu}</a></td>
      <td class="num">${fmt(p.prop)}</td><td class="num" style="color:#1e8449">${fmt(p.pago)}</td>
      <td class="num" style="color:#ca6f1e">${fmt(Math.max(0,p.prop-p.pago))}</td>
      <td><span class="pill ${L[1]}">${L[0]}</span></td></tr>`;
  }).join('');
  return `<table class="propt"><thead><tr><th>Bloco</th><th>Nº Proposta</th><th class="num">Solicitado</th><th class="num">Recebido</th><th class="num">A recuperar</th><th>Situação</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function drawCharts(m){
  Object.values(charts).forEach(c=>{try{c.destroy()}catch(e){}});charts={};
  const yrs=D.anos;
  charts.year=new Chart(document.getElementById('cYear'),{type:'bar',data:{labels:yrs,datasets:[
    {label:'Solicitado',data:yrs.map(a=>totYr(m,a).sol),backgroundColor:'rgba(26,82,118,.35)',borderRadius:3},
    {label:'Recebido',data:yrs.map(a=>totYr(m,a).apr),backgroundColor:'#1e8449',borderRadius:3}
  ]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+fmtK(c.raw)}}},scales:{y:{ticks:{callback:v=>fmtK(v)}},x:{grid:{display:false}}}}});
  const props=(m.props||[]);const cnt={APROVADO:0,PARCIAL:0,EM_ANALISE:0};
  props.forEach(p=>cnt[p.st]=(cnt[p.st]||0)+1);
  charts.status=new Chart(document.getElementById('cStatus'),{type:'doughnut',data:{labels:['Aprovado','Parcial','Em análise'],datasets:[{data:[cnt.APROVADO,cnt.PARCIAL,cnt.EM_ANALISE],backgroundColor:['#1e8449','#2471a3','#ca6f1e']}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{boxWidth:12,font:{size:11}}}}}});
}
const ANO=D.ano_drill;

// Diagnóstico em PDF real (jsPDF) -> compartilha no celular (Web Share API) ou baixa
function pdf(){
  const m=cur;if(!m)return;const a=yr();
  const c=comps(m,a), rec=recuperavel(c), perd=c.total-rec;
  const props=(m.props||[]).slice().sort((x,y)=>y.prop-x.prop);
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF({unit:'pt', format:'a4'});
  const W = doc.internal.pageSize.getWidth(), M=40; let y=46;
  doc.setFillColor(14,61,89); doc.rect(0,0,W,30,'F');
  doc.setTextColor(255); doc.setFont('helvetica','bold'); doc.setFontSize(12); doc.text('G3 HEALTH SERVICE', M, 20);
  doc.setFont('helvetica','normal'); doc.setFontSize(8); doc.text('Diagnóstico de captação SUS — custeio MAC/PAP', W-M, 20, {align:'right'});
  doc.setTextColor(14,61,89); doc.setFont('helvetica','bold'); doc.setFontSize(15); doc.text('DIAGNÓSTICO — '+m.mun+'/'+m.uf, M, y); y+=16;
  doc.setTextColor(110); doc.setFont('helvetica','normal'); doc.setFontSize(9);
  doc.text('IBGE '+m.ibge+(m.pop?' · '+m.pop.toLocaleString('pt-BR')+' hab':'')+' · período '+D.anos[0]+'–'+D.anos[D.anos.length-1]+' · gerado '+new Date().toLocaleDateString('pt-BR'), M, y); y+=16;
  doc.setFillColor(247,242,251); doc.roundedRect(M,y,W-2*M,48,4,4,'F');
  doc.setTextColor(125,60,152); doc.setFont('helvetica','bold'); doc.setFontSize(9);
  doc.text('CAPTAÇÃO COMPROMETIDA EM '+a+' (NÚMERO ÚNICO)', M+12, y+16);
  doc.setFontSize(20); doc.text(fmt(c.total), M+12, y+38);
  doc.setFont('helvetica','normal'); doc.setFontSize(9); doc.setTextColor(30,132,73); doc.text('Recuperável: '+fmt(rec), W-M-12, y+24, {align:'right'});
  doc.setTextColor(192,57,43); doc.text('Risco de perda: '+fmt(perd), W-M-12, y+38, {align:'right'});
  y+=62;
  doc.autoTable({startY:y, margin:{left:M,right:M},
    head:[['Composição do número único','Identificado','Recuperável','Risco perda']],
    body:[
      ['1 · Propostas MAC/PAP paradas ('+a+')', fmt(c.gap), fmt(c.gap*0.6), fmt(c.gap*0.4)],
      ['2 · Desconto FAF MAC do ano ('+a+')', fmt(c.desc), fmt(c.desc*0.5), fmt(c.desc*0.5)],
      ['TOTAL — número único', fmt(c.total), fmt(rec), fmt(perd)],
      ['Contexto · descontos 2012–22 (não somado)', fmt(c.hist), '—', '—'] ],
    styles:{fontSize:8,cellPadding:4}, headStyles:{fillColor:[14,61,89],textColor:255,fontSize:8},
    columnStyles:{1:{halign:'right'},2:{halign:'right'},3:{halign:'right'}},
    didParseCell:(d)=>{ if(d.section==='body'){ if(d.column.index===2)d.cell.styles.textColor=[30,132,73]; if(d.column.index===3)d.cell.styles.textColor=[192,57,43]; if(d.row.index===2){d.cell.styles.fontStyle='bold';d.cell.styles.fillColor=[247,242,251];} if(d.row.index===3)d.cell.styles.textColor=[150,150,150]; } } });
  y = doc.lastAutoTable.finalY + 14;
  doc.autoTable({startY:y, margin:{left:M,right:M},
    head:[['Ano','Solicitado','Recebido','A recuperar','% aprov.']],
    body: D.anos.map(yy=>{const tt=totYr(m,yy);return [String(yy), fmt(tt.sol), fmt(tt.apr), fmt(tt.rec), pct(tt.apr,tt.sol)+'%'];}),
    styles:{fontSize:8,cellPadding:4}, headStyles:{fillColor:[26,82,118],textColor:255,fontSize:8},
    columnStyles:{1:{halign:'right'},2:{halign:'right'},3:{halign:'right'},4:{halign:'right'}} });
  y = doc.lastAutoTable.finalY + 14;
  if(props.length){
    doc.autoTable({startY:y, margin:{left:M,right:M},
      head:[['Bloco','Nº Proposta','Solicitado','Recebido','A recuperar']],
      body: props.map(p=>[p.b.toUpperCase(), String(p.nu), fmt(p.prop), fmt(p.pago), fmt(Math.max(0,p.prop-p.pago))]),
      styles:{fontSize:7.5,cellPadding:3}, headStyles:{fillColor:[26,82,118],textColor:255,fontSize:7.5},
      columnStyles:{2:{halign:'right'},3:{halign:'right'},4:{halign:'right'}} });
  }
  const pages=doc.internal.getNumberOfPages();
  for(let i=1;i<=pages;i++){ doc.setPage(i); const ph=doc.internal.pageSize.getHeight();
    doc.setFontSize(7.5); doc.setTextColor(140);
    doc.text('G3 Health Service Ltda · CNPJ 31.652.744/0001-14 · gerson.gomes@proton.me · +55 61 99255-7690', M, ph-22);
    doc.text('Fonte: Consulta FNS + Portal FNS · valores em R$ · estimativa conservadora · pág. '+i+'/'+pages, M, ph-12); }
  const fname='Diagnostico_'+m.mun.replace(/ /g,'_')+'_'+m.uf+'.pdf';
  const blob=doc.output('blob'); const file=new File([blob],fname,{type:'application/pdf'});
  if(navigator.canShare && navigator.canShare({files:[file]})){
    navigator.share({files:[file], title:'Diagnóstico '+m.mun+'/'+m.uf, text:'Diagnóstico de captação SUS — '+m.mun+'/'+m.uf}).catch(()=>doc.save(fname));
  } else { doc.save(fname); }
}
function csv(){
  const m=cur;if(!m)return;const ay=yr();const cc=comps(m,ay);const rr=recuperavel(cc);
  let c='RASTREIO CAPTAÇÃO SUS — G3\n'+m.mun+'/'+m.uf+';IBGE '+m.ibge+'\n\n';
  c+='NUMERO UNICO ('+ay+');Identificado;Recuperavel;Risco perda\n';
  c+='1 Propostas paradas MAC/PAP;'+cc.gap.toFixed(2)+';'+(cc.gap*0.6).toFixed(2)+';'+(cc.gap*0.4).toFixed(2)+'\n';
  c+='2 Desconto FAF MAC do ano;'+cc.desc.toFixed(2)+';'+(cc.desc*0.5).toFixed(2)+';'+(cc.desc*0.5).toFixed(2)+'\n';
  c+='TOTAL numero unico;'+cc.total.toFixed(2)+';'+rr.toFixed(2)+';'+(cc.total-rr).toFixed(2)+'\n';
  c+='Contexto descontos 2012-22 (nao somado);'+cc.hist.toFixed(2)+';;\n\n';
  c+='Ano;Bloco;Solicitado;Recebido;A recuperar\n';
  D.anos.forEach(a=>{['mac','pap'].forEach(b=>{const d=blocoYr(m,b,a);c+=a+';'+b.toUpperCase()+';'+d.solicitado.toFixed(2)+';'+d.pago.toFixed(2)+';'+d.recuperar.toFixed(2)+'\n';});});
  c+='\nPropostas individuais '+ANO+'\nBloco;NuProposta;Solicitado;Recebido;A recuperar;Situacao\n';
  (m.props||[]).forEach(p=>{c+=p.b.toUpperCase()+';'+p.nu+';'+p.prop.toFixed(2)+';'+p.pago.toFixed(2)+';'+Math.max(0,p.prop-p.pago).toFixed(2)+';'+p.st+'\n';});
  const bl=new Blob(['﻿'+c],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(bl);a.download='Rastreio_'+m.mun.replace(/ /g,'_')+'_'+m.uf+'.csv';a.click();
}

// ---- Enviar o ranking filtrado (top municípios) pelo WhatsApp ----
function whatsappRanking(){
  const a=yr();const arr=filtered();
  if(!arr.length){alert('Nenhum município no filtro atual.');return;}
  const uf=document.getElementById('ufSel').value;
  const ordTxt={num:'captação comprometida',recup:'recuperável',percap:'habitante (per capita)',rec:'propostas paradas',desc:'desconto FAF',mun:'nome'}[sortKey]||'captação comprometida';
  const N=Math.min(10,arr.length);
  const L=[];
  L.push('*RAIO-X DE CAPTAÇÃO SUS — Ranking '+(uf||'Brasil')+'*');
  L.push('_Top '+N+' por '+ordTxt+' · exercício '+a+'_');
  L.push('');
  for(let i=0;i<N;i++){
    const m=arr[i];const c=comps(m,a);const rec=recuperavel(c);
    let line=(i+1)+'. *'+m.mun+'/'+m.uf+'* — '+fmt(c.total)+' (recup. '+fmt(rec)+')';
    if(sortKey==='percap') line+=' · '+fmtHab(perCap(m,a))+'/hab';
    L.push(line);
  }
  L.push('');
  L.push('_Número único = propostas MAC/PAP paradas + desconto FAF do ano._');
  L.push('Fonte: dados oficiais (Consulta FNS + Portal FNS)');
  L.push('');
  L.push('📞 *G3 Health Service* · +55 61 99255-7690');
  const text=encodeURIComponent(L.join('\n'));
  window.open('https://wa.me/?text='+text,'_blank');
}

// ---- Enviar diagnóstico do município pelo Signal ----
// Signal não tem link de mensagem pronta (wa.me). Usa-se a folha de
// compartilhamento do sistema (Web Share API); fallback = copiar p/ colar.
function signalShare(){
  const m=cur;if(!m)return;const a=yr();
  const c=comps(m,a), rec=recuperavel(c);
  const nProp=(m.props||[]).length;
  const L=[];
  L.push('RAIO-X DE CAPTAÇÃO SUS — '+m.mun+'/'+m.uf);
  L.push('Diagnóstico G3 Health Service · exercício '+a);
  L.push('');
  L.push('Captação comprometida (nº único): '+fmt(c.total));
  L.push('Recuperável estimado: '+fmt(rec));
  L.push('');
  L.push('Composição:');
  L.push('- Propostas MAC/PAP paradas: '+fmt(c.gap));
  L.push('- Desconto FAF MAC ('+a+'): '+fmt(c.desc));
  if(c.hist>0) L.push('- Contexto descontos 2012-22: '+fmt(c.hist));
  L.push('');
  L.push('Propostas de custeio analisadas: '+nProp);
  L.push('Fonte: dados oficiais (Consulta FNS + Portal FNS)');
  L.push('');
  L.push('G3 Health Service · +55 61 99255-7690');
  const txt=L.join('\n');
  if(navigator.share){
    navigator.share({title:'Raio-X SUS — '+m.mun+'/'+m.uf, text:txt})
      .catch(()=>{}); // usuário escolhe Signal na folha de compartilhamento
  } else if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(txt)
      .then(()=>alert('Mensagem COPIADA. O Signal não abre conversa por link, então abra o Signal e cole (Cmd/Ctrl+V ou segure o campo → Colar).'))
      .catch(()=>signalFallbackCopy(txt));
  } else {
    signalFallbackCopy(txt);
  }
}
function signalFallbackCopy(txt){
  const ta=document.createElement('textarea');ta.value=txt;ta.style.position='fixed';ta.style.opacity='0';
  document.body.appendChild(ta);ta.focus();ta.select();
  try{document.execCommand('copy');alert('Mensagem COPIADA — abra o Signal e cole.');}catch(e){prompt('Copie a mensagem e cole no Signal:',txt);}
  document.body.removeChild(ta);
}

// ---- Proposta de trabalho (cliente) em PDF ----
function propostaPDF(){
  const a=yr();
  const inMun=(document.getElementById('propMun').value||'').trim();
  const inSec=(document.getElementById('propSec').value||'').trim();
  const resp=(document.getElementById('propResp').value||'').trim()||'Gerson Gomes';
  const munNome = inMun || (cur?(cur.mun+'/'+cur.uf):'[Município / UF]');
  const hoje=new Date().toLocaleDateString('pt-BR');
  // investimento (honorário fixo mensal) conforme porte populacional
  const popMun = cur ? (cur.pop||0) : 0;
  const inv = investimento(popMun);
  const investHTML = popMun
    ? `Para o porte deste município (<b>${popMun.toLocaleString('pt-BR')} habitantes</b> · faixa ${faixaPop(popMun)}), o honorário fixo mensal em contrato de assessoria é de <b>${fmt(inv)}/mês</b>, sem acréscimo de percentual de êxito, pois a assessoria baseia-se em <b>eficiência por contrato</b> e não por produtividade.`
    : `O honorário fixo mensal em contrato de assessoria varia conforme o porte do município, <b>sem acréscimo de percentual de êxito</b>: a assessoria baseia-se em eficiência por contrato e não por produtividade. Selecione o município na aba Detalhe para gravar o valor exato.`;
  // diagnóstico preliminar com números reais se houver município selecionado
  let diagBlock='';
  if(cur){
    const c=comps(cur,a), rec=recuperavel(c), perd=c.total-rec;
    diagBlock=`
    <h2>3. Diagnóstico preliminar — ${cur.mun}/${cur.uf}</h2>
    <p>A partir de dados oficiais (Consulta FNS e Portal FNS), levantamento preliminar para o exercício de ${a}:</p>
    <table class="num">
      <tr><th>Indicador (${a})</th><th class="r">Valor</th></tr>
      <tr><td>Captação comprometida — <b>número único</b></td><td class="r b" style="color:#7d3c98">${fmt(c.total)}</td></tr>
      <tr><td>&nbsp;&nbsp;1 · Propostas MAC/PAP paradas (solicitado não pago)</td><td class="r">${fmt(c.gap)}</td></tr>
      <tr><td>&nbsp;&nbsp;2 · Desconto FAF MAC retido no ano</td><td class="r">${fmt(c.desc)}</td></tr>
      <tr><td><b>Recuperável estimado</b> (conservador)</td><td class="r b" style="color:#1e8449">${fmt(rec)}</td></tr>
      <tr><td>Contexto · descontos MAC acumulados 2012–2022</td><td class="r" style="color:#888">${fmt(c.hist)}</td></tr>
    </table>
    <p class="small">Números preliminares de triagem automatizada; a análise detalhada confirma valores e classifica cada proposta por recuperabilidade.</p>`;
  } else {
    diagBlock=`
    <h2>3. Diagnóstico preliminar</h2>
    <p>Na contratação, entregamos o levantamento dos valores de custeio MAC e PAP solicitados, recebidos e parados do município, a partir de dados oficiais (Consulta FNS e Portal FNS), com o número único de captação comprometida e a estimativa de recuperável.</p>`;
  }
  const secLine = inSec ? ('A/C '+inSec+'<br>') : '';
  const html=`<!DOCTYPE html><html lang="pt-BR"><head><meta charset="UTF-8">
  <title>Proposta de Trabalho — G3 Health Service</title>
  <style>
    @page{margin:18mm 16mm}
    body{font-family:Arial,Helvetica,sans-serif;font-size:11.5px;color:#222;line-height:1.5}
    .top{display:flex;justify-content:space-between;align-items:flex-start;border-bottom:3px solid #0e3d59;padding-bottom:10px;margin-bottom:14px}
    .brand{font-size:18px;font-weight:800;color:#0e3d59}
    .brand small{display:block;font-size:10px;font-weight:400;color:#666;margin-top:2px}
    .meta{text-align:right;font-size:10px;color:#555}
    h1{font-size:15px;color:#0e3d59;margin:6px 0 2px}
    .sub{font-size:11px;color:#666;margin-bottom:14px}
    .to{background:#f4f6f9;border-radius:6px;padding:9px 12px;margin-bottom:14px;font-size:11px}
    h2{font-size:12.5px;color:#1a5276;margin:16px 0 5px;border-bottom:1px solid #e1e6ec;padding-bottom:3px}
    p{margin:6px 0}
    ul,ol{margin:6px 0 6px 18px}li{margin:3px 0}
    table.num{width:100%;border-collapse:collapse;margin:8px 0;font-size:11px}
    table.num th{background:#0e3d59;color:#fff;padding:6px 8px;text-align:left;font-size:10px}
    table.num td{padding:6px 8px;border-bottom:1px solid #eee}
    table.num .r{text-align:right}table.num .b{font-weight:700}
    .steps{counter-reset:s}
    .step{margin:7px 0;padding-left:30px;position:relative}
    .step:before{counter-increment:s;content:counter(s);position:absolute;left:0;top:0;width:20px;height:20px;background:#1a5276;color:#fff;border-radius:50%;text-align:center;line-height:20px;font-size:11px;font-weight:700}
    .step b{color:#0e3d59}
    .deliv{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin:8px 0}
    .deliv div{border:1px solid #e1e6ec;border-radius:6px;padding:9px 11px}
    .deliv .t{font-weight:700;color:#1a5276;font-size:11px;margin-bottom:3px}
    .small{font-size:10px;color:#888}
    .invest{background:#f3fbf9;border-left:3px solid #1e8449;border-radius:6px;padding:10px 13px;margin:8px 0}
    .foot{margin-top:20px;border-top:1px solid #e1e6ec;padding-top:9px;font-size:9.5px;color:#888}
    .sign{margin-top:30px;display:flex;gap:40px;justify-content:space-between}
    .sign .col{flex:1}
    .sign .line{border-top:1px solid #555;margin-top:42px;padding-top:5px;font-size:10px;text-align:center;font-weight:700}
    .sign .role{font-size:8.5px;color:#888;text-align:center;margin-top:2px}
    @media print{.noprint{display:none}}
  </style></head><body>
  <div class="top">
    <div class="brand">G3 HEALTH SERVICE<small>Assessoria em captação de recursos federais do SUS</small></div>
    <div class="meta">CNPJ 31.652.744/0001-14<br>gerson.gomes@proton.me<br>+55 61 99255-7690<br>${hoje}</div>
  </div>

  <h1>PROPOSTA DE TRABALHO</h1>
  <div class="sub">Assessoria para recuperação de recursos de custeio MAC e PAP não captados</div>
  <div class="to"><b>À ${munNome}</b><br>Secretaria Municipal de Saúde / Fundo Municipal de Saúde<br>${secLine}Ref.: Diagnóstico e recuperação de repasses federais do SUS</div>

  <h2>1. Apresentação</h2>
  <p>A <b>G3 Health Service</b> é especializada em identificar e recuperar recursos federais do SUS que deixam de ser captados pelos municípios — especialmente no custeio da <b>Média e Alta Complexidade (MAC)</b> e da <b>Atenção Primária (PAP)</b>. Trabalhamos exclusivamente com <b>dados oficiais</b> do Ministério da Saúde, de forma auditável.</p>

  <h2>2. O problema que resolvemos</h2>
  <p>Todos os anos, municípios deixam de receber recursos a que teriam direito por motivos administrativos, e não por falta de teto:</p>
  <ul>
    <li><b>Propostas paradas</b> — pedidos de custeio MAC/PAP solicitados e não pagos, presos em análise.</li>
    <li><b>Recusas por erro</b> — propostas em diligência/pendência por falha documental, recuperáveis com correção.</li>
    <li><b>Descontos no FAF</b> — parcelas retidas no repasse fundo a fundo (bruto x líquido).</li>
    <li><b>Prazos e adesões perdidos</b> — programas e janelas de captação não aproveitados.</li>
  </ul>

  ${diagBlock}

  <h2>4. Metodologia — passo a passo</h2>
  <div class="steps">
    <div class="step"><b>Coleta oficial.</b> Levantamento de todas as propostas de custeio MAC e PAP e dos repasses FAF do município (Consulta FNS + Portal FNS).</div>
    <div class="step"><b>Triagem MAC/PAP.</b> Separação por bloco e por situação: aprovado, em análise, pendência/erro, não solicitado.</div>
    <div class="step"><b>Quantificação.</b> Cálculo do que o município deixou de captar — o número único de captação comprometida.</div>
    <div class="step"><b>Classificação por recuperabilidade.</b> Priorização entre recuperação rápida (erro a corrigir), acompanhamento (em análise) e novos pedidos.</div>
    <div class="step"><b>Dossiê por proposta.</b> Para cada caso recuperável: o que falta, prazo e responsável.</div>
    <div class="step"><b>Execução.</b> Correção e protocolo das propostas, com acompanhamento da mudança de situação no FNS.</div>
    <div class="step"><b>Comprovação.</b> Relatório periódico convertendo recursos de "parado" em "liberado", em R$.</div>
  </div>

  <h2>5. O que entregamos</h2>
  <div class="deliv">
    <div><div class="t">Raio-X de captação</div>Diagnóstico completo de MAC/PAP: solicitado, recebido e a recuperar, por ano.</div>
    <div><div class="t">Plano de recuperação</div>Lista priorizada do que dá para trazer de volta, com prazos e responsáveis.</div>
    <div><div class="t">Acompanhamento</div>Gestão das propostas até a liberação, com relatório de resultados.</div>
  </div>

  <h2>6. Fontes oficiais utilizadas</h2>
  <p class="small">Consulta FNS (consultafns.saude.gov.br) · Portal FNS (repasses FAF e descontos) · IBGE (população). Todos os números são oficiais e auditáveis pelo próprio gestor.</p>

  <h2>7. Investimento</h2>
  <div class="invest">${investHTML}</div>

  <h2>8. Próximos passos</h2>
  <ol>
    <li>Autorização para o diagnóstico (raio-X de captação).</li>
    <li>Apresentação dos resultados e do plano de recuperação priorizado.</li>
    <li>Início da execução e acompanhamento até a liberação dos recursos.</li>
  </ol>

  <div class="sign">
    <div class="col">
      <div class="line">${resp}</div>
      <div class="role">G3 Health Service — Contratada</div>
    </div>
    <div class="col">
      <div class="line">${inSec||'&nbsp;'}</div>
      <div class="role">Responsável — Secretaria Municipal de Saúde / Fundo Municipal de Saúde${(munNome&&munNome!=='[Município / UF]')?' · '+munNome:''} (Contratante)</div>
    </div>
  </div>

  <div class="foot">G3 Health Service Ltda · CNPJ 31.652.744/0001-14 · gerson.gomes@proton.me · +55 61 99255-7690 — Proposta gerada em ${hoje}. Estimativas de recuperabilidade conservadoras, confirmadas na análise detalhada.</div>
  </body></html>`;
  const w=window.open('','_blank','width=900,height=760');w.document.write(html);w.document.close();setTimeout(()=>w.print(),400);
}
renderOverview();
</script>
</body></html>"""

# ---- methodology markdown -> simple HTML ----
import re
md = Path("/Users/gersongomes/raiox/METODOLOGIA_ASSESSORIA.md").read_text()

def md_to_html(md):
    lines = md.split("\n")
    out = []
    i = 0
    in_tbl = False
    in_list = None
    def close_list():
        nonlocal in_list
        if in_list:
            out.append(f"</{in_list}>"); in_list = None
    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        # table
        if "|" in s and s.startswith("|"):
            close_list()
            cells = [c.strip() for c in s.strip("|").split("|")]
            if set("".join(cells).replace("-", "").replace(":", "")) == set():
                i += 1; continue  # separator row
            if not in_tbl:
                out.append("<table>"); in_tbl = True
                out.append("<tr>" + "".join(f"<th>{inl(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{inl(c)}</td>" for c in cells) + "</tr>")
            i += 1; continue
        elif in_tbl:
            out.append("</table>"); in_tbl = False
        if s.startswith("### "):
            close_list(); out.append(f"<h3>{inl(s[4:])}</h3>")
        elif s.startswith("## "):
            close_list(); out.append(f"<h2>{inl(s[3:])}</h2>")
        elif s.startswith("# "):
            close_list(); out.append(f"<h2>{inl(s[2:])}</h2>")
        elif s.startswith("> "):
            close_list(); out.append(f"<blockquote>{inl(s[2:])}</blockquote>")
        elif re.match(r"^\d+\.\s", s):
            if in_list != "ol":
                close_list(); out.append("<ol>"); in_list = "ol"
            item = re.sub(r"^\d+\.\s", "", s)
            out.append(f"<li>{inl(item)}</li>")
        elif s.startswith("- "):
            if in_list != "ul":
                close_list(); out.append("<ul>"); in_list = "ul"
            out.append(f"<li>{inl(s[2:])}</li>")
        elif s == "---":
            close_list()
        elif s == "":
            close_list()
        else:
            close_list(); out.append(f"<p>{inl(s)}</p>")
        i += 1
    if in_tbl: out.append("</table>")
    close_list()
    return "\n".join(out)

def inl(t):
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    t = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", t)
    return t

method_html = md_to_html(md)

# inline Chart.js + jsPDF (sem dependência de CDN -> abre offline, em qualquer máquina)
chartjs = (Path.home() / "raiox/vendor/chart.umd.js").read_text().replace("</script", "<\\/script")
jspdf = (Path.home() / "raiox/vendor/jspdf.umd.min.js").read_text().replace("</script", "<\\/script")
autotable = (Path.home() / "raiox/vendor/jspdf.autotable.min.js").read_text().replace("</script", "<\\/script")
out = HTML.replace("__CHARTJS__", "<script>\n" + chartjs + "\n</script>")
out = out.replace("__JSPDF__", "<script>\n" + jspdf + "\n</script>\n<script>\n" + autotable + "\n</script>")
out = out.replace("__DATA__", json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
out = out.replace("__METHOD__", method_html)
outpath = Path.home() / "Downloads/dashboard_propostas_mac_pap.html"
outpath.write_text(out, encoding="utf-8")
print(f"OK -> {outpath} ({outpath.stat().st_size//1024}KB) [Chart.js + jsPDF inline, 100% offline]")
