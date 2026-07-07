#!/usr/bin/env python3
"""
Monitora PAGAMENTO das propostas EXTRA-TETO cadastradas na CONTROLADORIA
(planilha Google) — ou seja, SOMENTE as linhas que têm o "Nº da Proposta"
preenchido. São essas as propostas captadas pela G3 (custeio MAC/PAP), pelas
quais a assessoria é remunerada. Pagamentos de outras propostas do mesmo
município NÃO entram (não somam para comissionamento).

Para cada proposta cadastrada, consulta o detalhe oficial no Consulta FNS
(obter-proposta). Se está paga (vlPago > 0) e ainda não foi avisada, dispara:
  - e-mail com assunto chamativo + tabela completa (parcela, data, valor, valor
    acumulado, ordem bancária, nº processo, localização) + portaria — no formato
    do Portal FNS;
  - registro na aba "Pagas" da planilha (via Apps Script action=registrarPagamento),
    que também destaca pago_em/valor_pago no lead.

Estado (idempotência) em estado_pagamentos.json: nuProposta -> {pago, pago_alertado}.
"""
import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fontes import consulta_fns_proposta as cf

CTRL_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vTMcZpgiHbci8FynfSa"
            "Q4wojiPxplxmSKbzhrwoAz1kE9L6bXiaUyWWAZ16vtq9ZBBObHd0xGTdaf6w/pub?output=csv")
BASE = Path(__file__).parent
ESTADO = BASE / "estado_pagamentos.json"
EMAIL_PAGAMENTO = BASE / "alerta_email_pagamento.txt"
EMAIL = BASE / "alerta_email.txt"  # trilha antiga (movimentações) — mantida vazia por ora
_savef = BASE / "ctrl_save_url.txt"
CTRL_SAVE_URL = _savef.read_text().strip() if _savef.exists() else ""


def _reais(v):
    return "R$ " + f"{float(v or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _epoch_br(ms):
    if not ms:
        return ""
    try:
        from datetime import datetime, timezone
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc).strftime("%d/%m/%Y")
    except Exception:
        return ""


def ler_controladoria():
    """Retorna as propostas EXTRA-TETO cadastradas (linhas COM nu_proposta).
    Usa parser CSV real (o campo observações pode ter vírgulas/aspas)."""
    txt = urllib.request.urlopen(CTRL_URL + "&_cb=" + str(id(object())), timeout=30).read().decode("utf-8")
    rows = list(csv.reader(io.StringIO(txt)))
    if not rows:
        return []
    hdr = [h.strip().lower() for h in rows[0]]

    def col(prefixo):
        for i, h in enumerate(hdr):
            if h.startswith(prefixo):
                return i
        return None

    iNP, iI, iM, iU = col("nu_prop"), col("ibge"), col("municipio"), col("uf")
    iR, iTp = col("responsavel"), col("tipo")
    if iNP is None:
        return []
    leads, vistos = [], set()
    for r in rows[1:]:
        def g(i):
            return (r[i].strip() if i is not None and i < len(r) else "")
        nu = g(iNP)
        if not nu or nu in vistos:
            continue
        vistos.add(nu)
        leads.append({
            "nu": nu, "ibge": g(iI)[:6], "municipio": g(iM), "uf": g(iU),
            "responsavel": g(iR), "tipo": g(iTp),
        })
    return leads


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
    leads = ler_controladoria()
    raw = json.loads(ESTADO.read_text()) if ESTADO.exists() else {}
    estado = {k: (v if isinstance(v, dict) else None) for k, v in raw.items()}
    primeira_vez = not ESTADO.exists()

    pagamentos_novos = []  # [{lead, det}]
    for lead in leads:
        nu = lead["nu"]
        try:
            det = cf.obter_proposta(nu)
        except Exception:
            det = {}
        if not det or not det.get("nuProposta"):
            continue
        pago = float(det.get("vlPago") or 0)
        antigo = estado.get(nu)
        ja_alertado = bool(antigo and antigo.get("pago_alertado"))
        if primeira_vez:
            estado[nu] = {"pago": pago, "pago_alertado": pago > 0}
        elif pago > 0 and not ja_alertado:
            estado[nu] = {"pago": pago, "pago_alertado": True}
            pagamentos_novos.append({"lead": lead, "det": det})
        else:
            estado[nu] = {"pago": pago, "pago_alertado": ja_alertado}

    ESTADO.write_text(json.dumps(estado, ensure_ascii=False, separators=(",", ":")))

    if pagamentos_novos:
        L = ["💰💰💰 PAGAMENTO(S) CONFIRMADO(S) — Propostas EXTRA-TETO (G3) 💰💰💰", ""]
        total_geral = 0.0
        for pn in pagamentos_novos:
            lead, det = pn["lead"], pn["det"]
            pagamentos = det.get("pagamentos") or []
            nu_portaria = det.get("nuPortaria") or ""
            dt_portaria = _epoch_br(det.get("dtPortaria"))
            situacao = ((det.get("situacao") or {}).get("descricaoSituacaoproposta")
                        or det.get("situacaoUltimaAnalise") or "")
            vl_pago_total = float(det.get("vlPago") or 0)
            tipo = det.get("coTipoProposta") or lead.get("tipo") or ""
            municipio = det.get("noMunicipio") or lead.get("municipio") or ""
            uf = det.get("sgUf") or lead.get("uf") or ""
            if not pagamentos and vl_pago_total > 0:
                pagamentos = [{"nuParcela": "(liberado)", "dtCriacaoSiafi": None, "vlLiquido": vl_pago_total,
                               "vlAcumulado": vl_pago_total, "nuOb": "", "nuProcesso": "", "localizacao": situacao}]
            L.append(f"📍 {municipio}/{uf} — {tipo} — Proposta {lead['nu']}")
            if lead.get("responsavel"):
                L.append(f"   Responsável (captador): {lead['responsavel']}")
            if situacao:
                L.append(f"   Situação: {situacao}")
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
                    "ibge": lead["ibge"], "municipio": municipio, "uf": uf,
                    "nu_proposta": lead["nu"], "tipo": tipo, "responsavel": lead.get("responsavel", ""),
                    "parcela": p.get("nuParcela", ""), "data_pagamento": _epoch_br(p.get("dtCriacaoSiafi")),
                    "valor_pagamento": f"{valor:.2f}", "valor_acumulado": f"{float(p.get('vlAcumulado') or 0):.2f}",
                    "ordem_bancaria": p.get("nuOb", ""), "nu_processo_pgto": p.get("nuProcesso", ""),
                    "localizacao_processo": p.get("localizacao", ""),
                    "nu_portaria": str(nu_portaria), "data_portaria": dt_portaria,
                })
            L.append(f"   🔗 https://consultafns.saude.gov.br/#/proposta/{lead['nu']}/detalhe")
            L.append("")
        L += [f"Total pago (soma das parcelas acima): {_reais(total_geral)}", "",
              "Painel: https://g3healthservice.github.io/raiox-captacao-sus/",
              "— Robô Raio-X SUS · G3 Health Service"]
        EMAIL_PAGAMENTO.write_text("\n".join(L), encoding="utf-8")
        print(f"TEM_PAGAMENTO=1  ({len(pagamentos_novos)} proposta(s) EXTRA-TETO paga(s))")
    else:
        if EMAIL_PAGAMENTO.exists():
            EMAIL_PAGAMENTO.unlink()
        print(f"TEM_PAGAMENTO=0  ({len(leads)} proposta(s) EXTRA-TETO monitorada(s))")

    # trilha antiga de "outras movimentações" desativada neste modelo (foco = pagamento das cadastradas)
    if EMAIL.exists():
        EMAIL.unlink()
    print("TEM_NOVOS=0")


if __name__ == "__main__":
    main()
