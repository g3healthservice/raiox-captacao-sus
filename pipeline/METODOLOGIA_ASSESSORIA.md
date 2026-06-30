# Rastreio de Captação SUS — Metodologia de Assessoria (prefeitura a prefeitura)
### G3 Health Service · Custeio MAC e PAP

> Objetivo: demonstrar, com dado oficial, **quanto a prefeitura/fundo de saúde deixou de receber** em custeio MAC e PAP, **onde o dinheiro está parado** e **quanto é recuperável** — e conduzir o secretário a um desfecho positivo (recuperação de recursos).

---

## 1. O fluxo de demonstração de valor (a lógica que convence o secretário)

O secretário não compra "consultoria". Ele compra **dinheiro que está na mesa e ele não viu.** A apresentação precisa seguir esta ordem psicológica:

| # | O que mostrar | Pergunta que responde | Efeito no secretário |
|---|---------------|----------------------|----------------------|
| 1 | **A foto atual** — quanto entrou de MAC/PAP | "Quanto eu recebo hoje?" | Reconhecimento ("é isso mesmo") |
| 2 | **O buraco** — quanto foi solicitado e está parado/recusado | "Tem dinheiro meu travado?" | Surpresa / tensão |
| 3 | **A causa** — por que parou (erro, pendência, prazo, falta de adesão) | "Por que não recebi?" | Entendimento (não é culpa dele sozinho) |
| 4 | **O recuperável** — quanto dá para trazer de volta | "Quanto eu recupero?" | Esperança / urgência |
| 5 | **O plano** — passo a passo + prazo + responsável | "Como faço?" | Confiança (você tem o caminho) |
| 6 | **O custo de não agir** — prazo que expira, recurso que devolve | "O que perco se não fizer nada?" | Decisão |

**Regra de ouro:** primeiro o número grande do *deixou de ganhar*, depois o *recuperável*. O gap cria a dor; o recuperável vende a solução.

---

## 2. De onde vem cada dado (fontes oficiais — tudo público)

| Dado | Fonte | O que extrai |
|------|-------|--------------|
| Propostas de custeio MAC/PAP (solicitado × pago × situação) | **Consulta FNS → Proposta** (`consultafns.saude.gov.br/#/proposta`) | Quanto foi pedido, quanto foi pago, em que fase está cada proposta |
| Repasse efetivo FAF (bruto × líquido × desconto) | **Portal FNS** (REPASSE-FAF-COM-POPULACAO) | Quanto realmente caiu na conta e quanto foi descontado |
| Saldo parado / descontos históricos | **Lista de Descontos FAF 2012–2022** | Recurso retido / risco de devolução |
| Pendências que travam pagamento | **Consulta FNS → Pendência** (por CNPJ do fundo) | O "erro" que está bloqueando o repasse |
| População (base de cálculo per capita) | **IBGE** | Comparar captação por habitante |

> Tudo é dado oficial e auditável. Isso é o que dá autoridade à apresentação: você não "acha", você **mostra a tela do Ministério da Saúde**.

---

## 3. Como ler a situação de cada proposta (a régua de classificação)

No Consulta FNS, cada proposta tem um **código de situação**. A leitura para custeio MAC/PAP:

| Situação (FNS) | Significado | Classificação G3 | Ação |
|----------------|-------------|------------------|------|
| `LIBERADO PAGAMENTO FNS` | Dinheiro liberado/pago | ✅ **APROVADO** | Conferir se caiu na conta |
| `EM ANÁLISE PELA ÁREA FINALÍSTICA/TÉCNICA` | Na fila, sem erro aparente | 🟡 **A RECUPERAR** | Acompanhar e empurrar prazo |
| `EM DILIGÊNCIA / PENDÊNCIA / DEVOLVIDO` | Travado por erro/documento | 🟠 **RECUSADO POR ERRO** | Corrigir e reapresentar (alto recuperável) |
| Proposta nem constituída / fora do prazo | Não chegou a ser pedido | 🔴 **DEIXOU DE PEDIR** | Montar proposta nova |

**Os três números que importam por proposta:**
- `vlProposta` = **solicitado** (o teto pedido)
- `vlPago` = **recebido** (o que efetivamente caiu)
- `vlProposta − vlPago` = **gap** (o que falta — o "deixou de ganhar" daquela proposta)

---

## 4. Passo a passo do processo de assessoria

### Passo 1 — Coleta (1 município por vez)
- Resolver o município (IBGE) e o CNPJ do Fundo Municipal de Saúde.
- Puxar **todas** as propostas de `CUSTEIO MAC` e `CUSTEIO PAP` dos últimos anos (ex.: 2024–2026).
- Puxar o repasse FAF efetivo (líquido × desconto) e o saldo parado.

### Passo 2 — Triagem MAC/PAP
- Separar por bloco (MAC × PAP) e por situação (aprovado / em análise / pendência / não pedido).
- Somar `solicitado`, `pago` e `gap` por bloco e por ano.

### Passo 3 — Quantificar o "deixou de ganhar"
- **Gap de custeio** = solicitado − pago (propostas paradas/recusadas).
- **Desconto MAC** = bruto − líquido no FAF (parcela retida).
- **Saldo parado** = recurso em conta sem execução (risco de devolução).
- Somar: este é o **número grande** da capa.

### Passo 4 — Classificar por recuperabilidade
- 🟠 **Recusado por erro** → recuperável alto (corrige e reapresenta).
- 🟡 **Em análise** → recuperável médio (acompanhamento/prazo).
- 🔴 **Não pedido / fora do prazo** → recuperável baixo (refazer no próximo ciclo).
- Estimativa conservadora: % recuperável e % perdido por categoria (ajustável caso a caso).

### Passo 5 — Montar o dossiê por proposta
Para cada proposta com gap, registrar: nº da proposta, bloco, valor, situação, **o que falta**, prazo e responsável. É o "checklist de recuperação".

### Passo 6 — Apresentar ao secretário (a reunião)
- Capa: 1 página — "Sua prefeitura deixou de receber **R$ X**; **R$ Y** é recuperável."
- Seguir o fluxo da seção 1 (foto → buraco → causa → recuperável → plano → custo de não agir).
- Terminar com **uma decisão pedida**: autorizar o plano de recuperação.

### Passo 7 — Executar e acompanhar
- Abrir/corrigir as propostas, protocolar, acompanhar a mudança de situação no FNS.
- Relatório mensal: "movemos R$ Z de *parado* para *liberado*."

---

## 5. O desfecho positivo (como amarrar)

O contrato/êxito se sustenta em três entregas concretas:
1. **Diagnóstico** (este rastreio) — mostra o tamanho do problema.
2. **Plano de recuperação** — lista priorizada do que dá para trazer de volta.
3. **Acompanhamento** — converter "parado" em "liberado" e provar o resultado em R$.

> Modelo de remuneração natural: parte fixa pelo diagnóstico/plano + **êxito sobre o recuperado** — alinha o interesse e remove o risco percebido pelo gestor.

---

*G3 Health Service Ltda · CNPJ 31.652.744/0001-14 · gerson.gomes@proton.me · +55 61 99255-7690*
*Fontes: Consulta FNS (consultafns.saude.gov.br) · Portal FNS · IBGE. Valores oficiais; estimativas de recuperabilidade são conservadoras e ajustáveis por caso.*
