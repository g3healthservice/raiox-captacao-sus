#!/usr/bin/env python3
"""
Une os shards de propostas (/tmp/prop_part_*.json) e cruza com os descontos FAF
(/tmp/multianos.json) para gerar UM NÚMERO ÚNICO por município:

  Captação comprometida = (1) Propostas MAC/PAP paradas  (solicitado - pago)
                        + (2) Desconto FAF MAC retido     (bruto - líquido)
                        + (3) Saldo parado histórico       (descontos 2012-2022)

Saída: /tmp/propostas_dataset.json  (consumido por gerar_dashboard_propostas.py)
"""
import glob
import json
import time
from pathlib import Path

# 1) une shards
muns = []
parts = sorted(glob.glob("/tmp/prop_part_*.json"))
anos = None
ano_drill = 2026
ufs = None
for p in parts:
    d = json.loads(Path(p).read_text())
    anos = d.get("anos", anos)
    ano_drill = d.get("ano_drill", ano_drill)
    muns.extend(d["municipios"])
print(f"shards: {len(parts)}  municípios (propostas): {len(muns)}")

# 2) índice FAF por ibge6
faf_idx = {}
for m in json.loads(Path("/tmp/multianos.json").read_text()):
    faf_idx[str(m["ibge"])] = m

ANOS_FAF = [str(a) for a in anos]  # alinhado aos anos de propostas

# 3) cruza
sem_faf = 0
for m in muns:
    f = faf_idx.get(str(m["ibge"]))
    if not f:
        m["faf"] = {"saldo": 0.0, "years": {}}
        sem_faf += 1
        continue
    yrs = {}
    for a in ANOS_FAF:
        y = f.get("years", {}).get(a) or {}
        desc = round(float(y.get("desc", 0) or 0), 2)
        # desconto real = bruto - líquido (>= desc reportado); usa o maior
        desc_calc = round(max(0.0, float(y.get("mac_b", 0) or 0) - float(y.get("mac_l", 0) or 0)), 2)
        yrs[a] = {
            "desc": max(desc, desc_calc),
            "mac_l": round(float(y.get("mac_l", 0) or 0), 2),
            "pap_l": round(float(y.get("pap_l", 0) or 0), 2),
            "total_l": round(float(y.get("total_l", 0) or 0), 2),
        }
    m["faf"] = {"saldo": round(float(f.get("saldo", 0) or 0), 2), "years": yrs}
    if not m.get("pop"):
        m["pop"] = f.get("pop", 0)

print(f"municípios sem match FAF: {sem_faf}")

# 4) ordena por número único do ano de referência (desc) p/ ranking default
# número único = propostas paradas + desconto FAF do ano (mesmo exercício).
# saldo 2012-22 é contexto acumulado, NÃO entra no total (evita dupla contagem/distorção).
def numero_unico(m, ano):
    a = m["anos"].get(str(ano), {})
    gap = a.get("mac", {}).get("recuperar", 0) + a.get("pap", {}).get("recuperar", 0)
    desc = m["faf"]["years"].get(str(ano), {}).get("desc", 0)
    return gap + desc

muns.sort(key=lambda m: numero_unico(m, ano_drill), reverse=True)

out = {
    "gerado_em": time.strftime("%Y-%m-%d %H:%M"),
    "anos": anos,
    "ano_drill": ano_drill,
    "ufs": sorted({m["uf"] for m in muns}),
    "fonte": "Consulta FNS (proposta) + Portal FNS (FAF/descontos)",
    "muns": muns,
}
OUT = Path("/tmp/propostas_dataset.json")
OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(f"OK -> {OUT}  ({OUT.stat().st_size//1024}KB)  UFs={len(out['ufs'])}")

# resumo nacional
tot = sum(numero_unico(m, ano_drill) for m in muns)
gap = sum(m["anos"].get(str(ano_drill), {}).get("mac", {}).get("recuperar", 0)
          + m["anos"].get(str(ano_drill), {}).get("pap", {}).get("recuperar", 0) for m in muns)
desc = sum(m["faf"]["years"].get(str(ano_drill), {}).get("desc", 0) for m in muns)
saldo = sum(m["faf"]["saldo"] for m in muns)
print(f"\nNÚMERO ÚNICO NACIONAL ({ano_drill}): R$ {tot:,.0f}  (= 1 + 2)")
print(f"  (1) propostas paradas: R$ {gap:,.0f}")
print(f"  (2) desconto FAF MAC : R$ {desc:,.0f}")
print(f"  [contexto] descontos acumulados 2012-22: R$ {saldo:,.0f} (não somado)")
print("\nTop 8 por número único:")
for m in muns[:8]:
    print(f"  {m['mun']}/{m['uf']}: R$ {numero_unico(m, ano_drill):,.0f}")
