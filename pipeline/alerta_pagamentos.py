#!/usr/bin/env python3
"""
Detecta MOVIMENTAÇÃO nas propostas de custeio MAC/PAP dos municípios da
CONTROLADORIA (planilha Google) e prepara resumo para envio por e-mail.

Duas trilhas de alerta, separadas:
  1) PAGAMENTO — quando uma proposta recebe um pagamento novo (ou o valor pago
     aumenta). Email com assunto chamativo + tabela completa (parcela, data,
     valor, valor acumulado, ordem bancária, processo, localização, portaria),
     no mesmo formato do Portal FNS. Também registra no Apps Script
     (action=registrarPagamento), que grava na aba "Pagas" da planilha e
     destaca pago_em/valor_pago no lead principal.
  2) Outras movimentações — processo constituído, valor da proposta alterado
     etc. Email consolidado padrão (como já existia).

Anos monitorados = ano vigente + ano anterior (dinâmico).
Estado em estado_pagamentos.json (nuProposta -> assinatura). Só envia quando
há movimentação real; consolida várias num único e-mail por trilha.
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
EMAIL_PAGAMENTO = BASE / "alerta_email_pagamento.txt"
_savef = BASE / "ctrl_save_url.txt"
CTRL_SAVE_URL = _savef.read_text().strip() if _savef.exists() else ""


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


def _descreve_outro(old, new):
    """Descreve movimentações que NÃO são pagamento (processo, valor da proposta)."""
    if old is None:
        return None
    msgs = []
    if new["const"] and not old.get("const", False):
        msgs.append("processo constituído")
    if new["prop"] != old.get("prop", new["prop"]):
        msgs.append(f"valor da proposta alterado: {_reais(old.get('prop', 0))} → {_reais(new['prop'])}")
    if new["pago"] < old.get("pago", 0):
        msgs.append(f"valor pago ajustado para {_reais(new['pago'])}")
    return " · ".join(msgs) if msgs else None


def _eh_pagamento_novo(old, new):
    if old is None:
        return False
    return new["pago"] > old.get("pago", 0) or new["npag"] > old.get("npag", 0)


def ler_controladoria():
    """Retorna (municipios únicos [(ibge,nome)], responsavel_por_proposta {nu: {responsavel, tipo}})."""
    txt = urllib.request.urlopen(CTRL_URL, timeout=30).read().decode("utf-8")
    linhas = [l for l in txt.splitlines() if l.strip()]
    hdr = [h.strip().lower() for h in linhas[0].split(",")]
    iI = next((i for i, h in enumerate(hdr) if h.startswith("ibge")), 0)
    iM = next((i for i, h in enumerate(hdr) if h.startswith("municipio")), 1)
    iR = next((i for i, h in enumerate(hdr) if h.startswith("responsavel")), None)
    iNP = next((i for i, h in enumerate(hdr) if h.startswith("nu_prop")), None)
    iTp = next((i for i, h in enumerate(hdr) if h.startswith("tipo")), None)
    vistos = {}
    por_proposta = {}
    for l in linhas[1:]:
        c = l.split(",")
        ibge = c[iI].strip()[:6] if iI < len(c) else ""
        nome = c[iM].strip() if iM < len(c) else ""
        if ibge and ibge not in vistos:
            vistos[ibge] = nome
        nu = c[iNP].strip() if iNP is not None and iNP < len(c) else ""
        if nu:
            por_proposta[nu] = {
                "responsavel": c[iR].strip() if iR is not None and iR < len(c) else "",
                "tipo": c[iTp].strip() if iTp is not None and iTp < len(c) else "",
            }
    return list(vistos.items()), por_proposta


def _registrar_pagamento_sheet(payload):
    if not CTRL_SAVE_URL:
        return
    try:
        req = urllib.request.Request(
            CTRL_SAVE_URL, data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "text/plain;charset=utf-8"}, method="POST")
        urllib.request.urlopen(req, timeout=30).read()
    except Exception:
        pass  # não bloqueia o alerta se a planilha falhar


def main():
    muns, por_proposta = ler_controladoria()
    raw = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    estado = {k: (v if isinstance(v, dict) else None) for k, v in raw.items()}
    primeira_vez = not ESTADO.exists()
    movs_outros = []
    pagamentos_novos = []

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
                    if not primeira_vez and _eh_pagamento_novo(antigo, novo):
                        info = por_proposta.get(nu, {})
                        pagamentos_novos.append({
                            "mun": nome, "uf": it.get("sgUf", ""), "nu": nu, "bloco": tp, "ano": ano,
                            "responsavel": info.get("responsavel", ""), "ibge": ibge,
                        })
                    elif not primeira_vez:
                        desc = _descreve_outro(antigo, novo)
                        if desc:
                            movs_outros.append({"mun": nome, "uf": it.get("sgUf", ""), "nu": nu,
                                                 "bloco": tp, "ano": ano, "desc": desc})
                    estado[nu] = novo

    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, separators=(",", ":")))

    tem_algo = False

    # ---- Trilha 1: PAGAMENTO (e-mail chamativo + tabela FNS + registro na aba Pagas) ----
    if pagamentos_novos:
        tem_algo = True
        L = ["💰💰💰 PAGAMENTO(S) CONFIRMADO(S) — Raio-X SUS 💰💰💰", ""]
        total_geral = 0.0
        for pv in pagamentos_novos:
            try:
                detalhe = cf.obter_proposta(pv["nu"])
            except Exception:
                detalhe = {}
            pagamentos = detalhe.get("pagamentos") or []
            nu_portaria = detalhe.get("nuPortaria") or ""
            dt_portaria_ms = detalhe.get("dtPortaria")
            dt_portaria = _epoch_br(dt_portaria_ms)
            L.append(f"📍 {pv['mun']}/{pv['uf']} — {pv['bloco']} — Proposta {pv['nu']}")
            if pv["responsavel"]:
                L.append(f"   Responsável: {pv['responsavel']}")
            if nu_portaria:
                L.append(f"   Portaria nº {nu_portaria}" + (f" de {dt_portaria}" if dt_portaria else ""))
            L.append("   Parcela | Data Pagamento | Valor Pagamento | Valor Acumulado | Ordem Bancária | Nº Processo Pgto | Localização")
            for p in pagamentos:
                valor = float(p.get("vlLiquido") or 0)
                total_geral += valor
                L.append(
                    f"   {p.get('nuParcela','')} | {_epoch_br(p.get('dtCriacaoSiafi'))} | "
                    f"{_reais(valor)} | {_reais(p.get('vlAcumulado'))} | {p.get('nuOb','')} | "
                    f"{p.get('nuProcesso','')} | {p.get('localizacao','')}"
                )
                _registrar_pagamento_sheet({
                    "token": "g3ctrl2026", "action": "registrarPagamento",
                    "ibge": pv["ibge"], "municipio": pv["mun"], "uf": pv["uf"],
                    "nu_proposta": pv["nu"], "tipo": pv["bloco"], "responsavel": pv["responsavel"],
                    "parcela": p.get("nuParcela", ""), "data_pagamento": _epoch_br(p.get("dtCriacaoSiafi")),
                    "valor_pagamento": f"{valor:.2f}", "valor_acumulado": f"{float(p.get('vlAcumulado') or 0):.2f}",
                    "ordem_bancaria": p.get("nuOb", ""), "nu_processo_pgto": p.get("nuProcesso", ""),
                    "localizacao_processo": p.get("localizacao", ""),
                    "nu_portaria": str(nu_portaria), "data_portaria": dt_portaria,
                })
            L.append(f"   🔗 https://consultafns.saude.gov.br/#/proposta/{pv['nu']}/detalhe")
            L.append("")
        L += [f"Total pago (soma das parcelas acima): {_reais(total_geral)}", "",
              "Painel: https://g3healthservice.github.io/raiox-captacao-sus/",
              "— Robô Raio-X SUS · G3 Health Service"]
        EMAIL_PAGAMENTO.write_text("\n".join(L), encoding="utf-8")
        print(f"TEM_PAGAMENTO=1  ({len(pagamentos_novos)} pagamento(s))")
    else:
        if EMAIL_PAGAMENTO.exists():
            EMAIL_PAGAMENTO.unlink()
        print("TEM_PAGAMENTO=0")

    # ---- Trilha 2: outras movimentações (formato já existente) ----
    if movs_outros:
        tem_algo = True
        L = [f"MOVIMENTAÇÃO — custeio MAC/PAP ({'/'.join(map(str, ANOS))})", ""]
        for mv in movs_outros:
            L.append(f"• {mv['mun']}/{mv['uf']} — {mv['bloco']} {mv['ano']}")
            L.append(f"    {mv['desc']}")
            L.append(f"    Proposta {mv['nu']} · https://consultafns.saude.gov.br/#/proposta/{mv['nu']}/detalhe")
        L += ["", f"Total de movimentações: {len(movs_outros)}",
              "", "Painel: https://g3healthservice.github.io/raiox-captacao-sus/",
              "— Robô Raio-X SUS · G3 Health Service"]
        EMAIL.write_text("\n".join(L), encoding="utf-8")
        print(f"TEM_NOVOS=1  ({len(movs_outros)} movimentação(ões))")
    else:
        if EMAIL.exists():
            EMAIL.unlink()
        motivo = "baseline registrado" if primeira_vez else "sem movimentação"
        print(f"TEM_NOVOS=0  ({motivo}; {len(muns)} municípios · anos {ANOS})")


def _epoch_br(ms):
    if not ms:
        return ""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).strftime("%d/%m/%Y")
    except Exception:
        return ""


if __name__ == "__main__":
    main()
