#!/usr/bin/env python3
"""
Detecta MOVIMENTAÇÃO nas propostas de custeio MAC/PAP dos municípios da
CONTROLADORIA (planilha Google) e prepara resumo para envio por e-mail.

Movimentação = qualquer mudança em: valor da proposta, valor pago, valor a pagar,
processo constituído ou nº de pagamentos registrados (não só "pago").

Anos monitorados = ano vigente + ano anterior (dinâmico).
Estado em estado_pagamentos.json (nuProposta -> assinatura). Só envia quando há
movimentação; consolida várias num único e-mail.
"""
import json
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fontes import consulta_fns_proposta as cf

CTRL_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vTMcZpgiHbci8FynfSa"
            "Q4wojiPxplxmSKbzhrwoAz1kE9L6bXiaUyWWAZ16vtq9ZBBObHd0xGTdaf6w/pub?output=csv")
_Y = date.today().year
ANOS = [_Y - 1, _Y]           # ano anterior + ano vigente (dinâmico)
TIPOS = ["CUSTEIO MAC", "CUSTEIO PAP"]
BASE = Path(__file__).parent
ESTADO = BASE / "estado_pagamentos.json"
EMAIL = BASE / "alerta_email.txt"


def _reais(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _sig(it):
    return {
        "prop": float(it.get("vlProposta") or 0),
        "pago": float(it.get("vlPago") or 0),
        "pagar": float(it.get("vlPagar") or 0),
        "const": bool(it.get("constituidoProcesso")),
        "npag": len(it.get("pagamentos") or []),
    }


def _descreve(old, new):
    """Descreve a movimentação comparando assinatura antiga e nova."""
    if old is None:
        return None  # proposta nova entra no baseline sem alertar
    msgs = []
    if new["pago"] > old.get("pago", 0):
        msgs.append(f"PAGAMENTO +{_reais(new['pago'] - old.get('pago', 0))} (pago total {_reais(new['pago'])})")
    elif new["pago"] < old.get("pago", 0):
        msgs.append(f"valor pago ajustado para {_reais(new['pago'])}")
    if new["npag"] > old.get("npag", 0):
        msgs.append("novo pagamento registrado")
    if new["const"] and not old.get("const", False):
        msgs.append("processo constituído")
    if new["prop"] != old.get("prop", new["prop"]):
        msgs.append(f"valor da proposta alterado: {_reais(old.get('prop', 0))} → {_reais(new['prop'])}")
    return " · ".join(msgs) if msgs else None


def ler_controladoria():
    txt = urllib.request.urlopen(CTRL_URL, timeout=30).read().decode("utf-8")
    linhas = [l for l in txt.splitlines() if l.strip()]
    hdr = [h.strip().lower() for h in linhas[0].split(",")]
    iI = next((i for i, h in enumerate(hdr) if h.startswith("ibge")), 0)
    iM = next((i for i, h in enumerate(hdr) if h.startswith("municipio")), 1)
    out = []
    for l in linhas[1:]:
        c = l.split(",")
        ibge = c[iI].strip()[:6] if iI < len(c) else ""
        nome = c[iM].strip() if iM < len(c) else ""
        if ibge:
            out.append((ibge, nome))
    return out


def main():
    muns = ler_controladoria()
    raw = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    # migração de formato antigo ({nu: pago_float}) -> baseline sem alertar
    estado = {}
    for k, v in raw.items():
        estado[k] = v if isinstance(v, dict) else None
    primeira_vez = not ESTADO.exists()
    movs = []
    for ibge, nome in muns:
        for ano in ANOS:
            for tp in TIPOS:
                try:
                    itens = cf.consultar_individuais(ibge, ano, tp)
                except Exception:
                    itens = []
                for it in itens:
                    nu = str(it.get("nuProposta") or "")
                    if not nu:
                        continue
                    novo = _sig(it)
                    antigo = estado.get(nu)
                    desc = None if primeira_vez else _descreve(antigo, novo)
                    if desc:
                        movs.append({"mun": nome, "uf": it.get("sgUf", ""), "nu": nu,
                                     "bloco": tp, "ano": ano, "desc": desc})
                    estado[nu] = novo

    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, separators=(",", ":")))

    if movs:
        L = [f"MOVIMENTAÇÃO — custeio MAC/PAP ({'/'.join(map(str, ANOS))})", ""]
        for mv in movs:
            L.append(f"• {mv['mun']}/{mv['uf']} — {mv['bloco']} {mv['ano']}")
            L.append(f"    {mv['desc']}")
            L.append(f"    Proposta {mv['nu']} · https://consultafns.saude.gov.br/#/proposta/{mv['nu']}/detalhe")
        L += ["", f"Total de movimentações: {len(movs)}",
              "", "Painel: https://g3healthservice.github.io/raiox-captacao-sus/#k=eyJwZXJtIjp0cnVlLCJuIjoiRzMifQ.c6brfm",
              "— Robô Raio-X SUS · G3 Health Service"]
        EMAIL.write_text("\n".join(L), encoding="utf-8")
        print(f"TEM_NOVOS=1  ({len(movs)} movimentação(ões))")
    else:
        if EMAIL.exists():
            EMAIL.unlink()
        motivo = "baseline registrado" if primeira_vez else "sem movimentação"
        print(f"TEM_NOVOS=0  ({motivo}; {len(muns)} municípios · anos {ANOS})")


if __name__ == "__main__":
    main()
