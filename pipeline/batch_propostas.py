#!/usr/bin/env python3
"""
Batch: rastreia propostas de custeio MAC/PAP no Consulta FNS para uma lista de UFs.
Gera dataset para o dashboard de propostas.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fontes import consulta_fns_proposta as cf

UFS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["GO", "DF"]
ANOS = [2024, 2025, 2026]
ANO_DRILL = 2026
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/propostas_dataset.json")
# sharding: argv[3]="i/n" processa fatia i de n (para rodar workers em paralelo)
SHARD_I, SHARD_N = 0, 1
if len(sys.argv) > 3 and "/" in sys.argv[3]:
    SHARD_I, SHARD_N = (int(x) for x in sys.argv[3].split("/"))

# população por ibge6 (do dataset multianos já existente)
pop_by_ibge = {}
try:
    for m in json.loads(Path("/tmp/multianos.json").read_text()):
        pop_by_ibge[str(m["ibge"])] = m.get("pop", 0)
except Exception:
    pass

# lista de municípios IBGE
mun_all = json.loads((Path.home() / "raiox/cache/ibge_municipios.json").read_text())
def _uf_de(m):
    try:
        return m["microrregiao"]["mesorregiao"]["UF"]["sigla"]
    except (TypeError, KeyError):
        pass
    try:
        return m["regiao-imediata"]["regiao-intermediaria"]["UF"]["sigla"]
    except (TypeError, KeyError):
        return None

TODAS = UFS == ["ALL"]
alvo = []
for m in mun_all:
    uf = _uf_de(m)
    if TODAS or uf in UFS:
        ibge7 = str(m["id"])
        alvo.append({"uf": uf, "nome": m["nome"].upper(), "ibge6": ibge7[:6], "ibge7": ibge7,
                     "capital": False})

if SHARD_N > 1:
    alvo = alvo[SHARD_I::SHARD_N]

print(f"UFs={UFS}  shard={SHARD_I}/{SHARD_N}  municípios alvo={len(alvo)}  anos={ANOS}  out={OUT}", flush=True)

# DF / capitais -> esfera ESTADUAL
CAPITAIS_IBGE6 = {"530010", "520870"}  # Brasília, Goiânia (Goiânia recebe municipal; Brasília não)
ESFERA_ESTADUAL_IBGE6 = {"530010"}

resultado = []
t0 = time.time()
for i, mun in enumerate(alvo, 1):
    esfera = "ESTADUAL" if mun["ibge6"] in ESFERA_ESTADUAL_IBGE6 else None
    rec = {
        "uf": mun["uf"], "mun": mun["nome"], "ibge": mun["ibge6"], "ibge7": mun["ibge7"],
        "pop": pop_by_ibge.get(mun["ibge6"], 0),
        "anos": {}, "props": [],
    }
    def _round(d):
        return {
            "solicitado": round(d["solicitado"], 2), "pago": round(d["pago"], 2),
            "recuperar": round(d["recuperar"], 2),
            "cust": {"sol": round(d["cust"]["sol"], 2), "pago": round(d["cust"]["pago"], 2)},
            "incr": {"sol": round(d["incr"]["sol"], 2), "pago": round(d["incr"]["pago"], 2)},
        }
    try:
        r = cf.rastrear_municipio(mun["ibge6"], ANOS, esfera)
        for ano, d in r["anos"].items():
            rec["anos"][str(ano)] = {b: _round(d[b]) for b in ("mac", "pap")}
    except Exception as e:
        print(f"  ! {mun['nome']} grouped err: {e}", flush=True)

    # drill-down individuais de CUSTEIO (a parte recuperável) no ano atual
    tem_custeio = any(
        rec["anos"].get(str(ANO_DRILL), {}).get(b, {}).get("cust", {}).get("sol", 0) > 0
        for b in ("mac", "pap")
    )
    if tem_custeio:
        for bloco, tp in (("mac", "CUSTEIO MAC"), ("pap", "CUSTEIO PAP")):
            try:
                items = cf.consultar_individuais(mun["ibge6"], ANO_DRILL, tp, None, esfera)
                for it in items:
                    prop = float(it.get("vlProposta") or 0)
                    pago = float(it.get("vlPago") or 0)
                    if prop <= 0 and pago <= 0:
                        continue
                    if pago >= prop and prop > 0:
                        st = "APROVADO"
                    elif pago > 0:
                        st = "PARCIAL"
                    else:
                        st = "EM_ANALISE"
                    rec["props"].append({
                        "nu": it.get("nuProposta"),
                        "b": bloco,
                        "prop": round(prop, 2),
                        "pago": round(pago, 2),
                        "st": st,
                    })
                time.sleep(cf.THROTTLE)
            except Exception as e:
                print(f"  ! {mun['nome']} {tp} drill err: {e}", flush=True)

    resultado.append(rec)
    if i % 20 == 0 or i == len(alvo):
        el = time.time() - t0
        print(f"  [{i}/{len(alvo)}] {mun['uf']}/{mun['nome']}  ({el:.0f}s)", flush=True)

OUT.write_text(json.dumps({
    "gerado_em": time.strftime("%Y-%m-%d %H:%M"),
    "ufs": UFS, "anos": ANOS, "ano_drill": ANO_DRILL,
    "fonte": "consultafns.saude.gov.br/recursos/proposta",
    "municipios": resultado,
}, ensure_ascii=False, separators=(",", ":")))

# resumo
tot_sol = sum(m["anos"].get("2026", {}).get("mac", {}).get("solicitado", 0)
              + m["anos"].get("2026", {}).get("pap", {}).get("solicitado", 0) for m in resultado)
tot_pago = sum(m["anos"].get("2026", {}).get("mac", {}).get("pago", 0)
               + m["anos"].get("2026", {}).get("pap", {}).get("pago", 0) for m in resultado)
print(f"\nOK -> {OUT}  ({OUT.stat().st_size//1024}KB)")
print(f"2026 custeio MAC+PAP: solicitado R$ {tot_sol:,.0f} | pago R$ {tot_pago:,.0f} | a recuperar R$ {tot_sol-tot_pago:,.0f}")
print(f"municípios com propostas individuais 2026: {sum(1 for m in resultado if m['props'])}")
