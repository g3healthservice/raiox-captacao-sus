"""
Rastreio de PROPOSTAS de custeio (MAC e PAP) no Consulta FNS.
Fonte: https://consultafns.saude.gov.br/#/proposta  (API Restangular interna)

Endpoints descobertos (engenharia reversa do SPA AngularJS, app/pages/proposta):
  GET /recursos/proposta/consultar?ano=&coMunicipioIbge=&coEsfera=&tpProposta=&tpRecurso=&page=&count=
      -> resultado.itensPagina[], resultado.totalItens
      Sem tpProposta: retorna AGRUPADO por (coTipoProposta, dsTipoRecurso) com vlProposta e vlPago somados.
      Com tpProposta+tpRecurso: retorna PROPOSTAS INDIVIDUAIS com nuProposta.
  GET /recursos/proposta/obter-proposta?nuProposta=
      -> resultado{} com situacao, pagamentos[], vlEmpenhado, vlPago, vlPagar, constituidoProcesso

coMunicipioIbge usa 6 dígitos (sem dígito verificador). Brasília/capitais => coEsfera=ESTADUAL.

Classificação de situação (codigoSituacaoProjeto):
  67  = LIBERADO PAGAMENTO FNS         -> APROVADO/PAGO
  26,27,30,55,62 = EM ANALISE ...      -> EM ANÁLISE (a recuperar / acompanhar)
  demais / diligência / devolução      -> PENDÊNCIA (risco de perda; precisa correção)
"""

import json
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional

BASE = "https://consultafns.saude.gov.br/recursos/proposta"
HDRS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://consultafns.saude.gov.br/",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE

THROTTLE = 0.08

# Situações que significam dinheiro liberado
COD_LIBERADO = {67}
# Situações claramente "em análise"
COD_ANALISE = {26, 27, 30, 55, 62}


def _get(url: str) -> dict:
    req = urllib.request.Request(url, headers=HDRS)
    with urllib.request.urlopen(req, timeout=30, context=_CTX) as r:
        return json.loads(r.read().decode("utf-8"))


def consultar_agrupado(co_ibge6: str, ano: int, esfera: Optional[str] = None) -> list:
    """Lista agrupada por tipo de proposta (com vlProposta e vlPago somados)."""
    params = {"ano": ano, "coMunicipioIbge": co_ibge6, "page": 1, "count": 100}
    if esfera:
        params["coEsfera"] = esfera
    data = _get(f"{BASE}/consultar?" + urllib.parse.urlencode(params))
    return data.get("resultado", {}).get("itensPagina", [])


def consultar_individuais(co_ibge6: str, ano: int, tp_proposta: str,
                          tp_recurso: Optional[str] = None, esfera: Optional[str] = None) -> list:
    """Propostas individuais (com nuProposta) de um tipo.
    Omitindo tp_recurso, retorna todas as propostas do tipo (todos os recursos)."""
    params = {
        "ano": ano, "coMunicipioIbge": co_ibge6,
        "tpProposta": tp_proposta,
        "page": 1, "count": 300,
    }
    if tp_recurso:
        params["tpRecurso"] = tp_recurso
    if esfera:
        params["coEsfera"] = esfera
    data = _get(f"{BASE}/consultar?" + urllib.parse.urlencode(params))
    return data.get("resultado", {}).get("itensPagina", [])


def obter_proposta(nu_proposta: str) -> dict:
    data = _get(f"{BASE}/obter-proposta?nuProposta={nu_proposta}")
    return data.get("resultado", {})


def classificar_situacao(cod: Optional[int]) -> str:
    if cod in COD_LIBERADO:
        return "APROVADO"
    if cod in COD_ANALISE:
        return "EM_ANALISE"
    if cod is None:
        return "EM_ANALISE"
    return "PENDENCIA"


def classificar_bloco(tipo: str):
    """Retorna (bloco, origem) onde bloco in {mac,pap} e origem in {C(usteio),I(ncremento)}."""
    t = (tipo or "").upper()
    if t.startswith("CUSTEIO MAC"):
        return "mac", "C"
    if t.startswith("INCREMENTO MAC"):
        return "mac", "I"
    if t.startswith("CUSTEIO PAP"):
        return "pap", "C"
    if t.startswith("INCREMENTO PAP"):
        return "pap", "I"
    return None, None


def rastrear_municipio(co_ibge6: str, anos: list, esfera: Optional[str] = None) -> dict:
    """
    Rastreio de custeio MAC e PAP de um município (CUSTEIO + INCREMENTO).
    Retorna por ano: por bloco solicitado/pago/recuperar e split custeio/incremento.
    """
    resultado = {"co_ibge6": co_ibge6, "anos": {}}
    for ano in anos:
        rows = consultar_agrupado(co_ibge6, ano, esfera)
        ano_d = {"mac": _zero(), "pap": _zero()}
        for it in rows:
            bloco, origem = classificar_bloco(it.get("coTipoProposta"))
            if not bloco:
                continue
            prop = float(it.get("vlProposta") or 0)
            pago = float(it.get("vlPago") or 0)
            ano_d[bloco]["solicitado"] += prop
            ano_d[bloco]["pago"] += pago
            sub = "cust" if origem == "C" else "incr"
            ano_d[bloco][sub]["sol"] += prop
            ano_d[bloco][sub]["pago"] += pago
        for b in ("mac", "pap"):
            ano_d[b]["recuperar"] = max(0.0, ano_d[b]["solicitado"] - ano_d[b]["pago"])
        resultado["anos"][ano] = ano_d
        time.sleep(THROTTLE)
    return resultado


def _zero():
    return {"solicitado": 0.0, "pago": 0.0, "recuperar": 0.0,
            "cust": {"sol": 0.0, "pago": 0.0}, "incr": {"sol": 0.0, "pago": 0.0}}


if __name__ == "__main__":
    import sys
    ibge = sys.argv[1] if len(sys.argv) > 1 else "520870"  # Goiânia
    r = rastrear_municipio(ibge, [2024, 2025, 2026])
    print(json.dumps(r, ensure_ascii=False, indent=2))
