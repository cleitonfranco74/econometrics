"""Gera os dados simulados usados nos Conteúdos 3 a 8.

Todos os dados são FICTÍCIOS e construídos com efeitos conhecidos, para que o
aluno possa comparar a estimativa com o "valor verdadeiro".
Uso:  python gerar_dados.py   (requer numpy e pandas)
"""
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parent
rng = np.random.default_rng(2026)


def salvar(df, pasta, nome):
    destino = BASE / pasta / "dados"
    destino.mkdir(parents=True, exist_ok=True)
    df.to_csv(destino / nome, index=False)
    print(f"{pasta}/dados/{nome}: {len(df)} linhas")


# ---------------------------------------------------------------------------
# Conteúdo 3 — publicidade e vendas (regressão simples)
# Efeito causal verdadeiro: cada R$ 1 mil em publicidade gera R$ 2,5 mil em
# vendas. O tamanho da empresa afeta publicidade E vendas (confundidor).
# ---------------------------------------------------------------------------
n = 120
tamanho = rng.normal(50, 15, n).clip(10)                  # nº de funcionários (dezenas)
publicidade = (2 + 0.20 * tamanho + rng.normal(0, 3, n)).clip(0.5)
vendas = 40 + 2.5 * publicidade + 3.0 * tamanho + rng.normal(0, 25, n)
salvar(pd.DataFrame({"empresa": range(1, n + 1),
                     "publicidade": publicidade.round(2),
                     "vendas": vendas.round(1),
                     "tamanho": tamanho.round(1)}),
       "03-correlacao-causalidade-regressao", "publicidade_vendas.csv")

# ---------------------------------------------------------------------------
# Conteúdo 4 — salários (regressão múltipla e viés de variável omitida)
# log(salário) = 1,2 + 0,08 educ + 0,03 exper − 0,0005 exper² − 0,15 mulher
#                + 0,10 habilidade + u
# ---------------------------------------------------------------------------
n = 600
habilidade = rng.normal(0, 1, n)
educ = np.clip(np.round(12 + 2.0 * habilidade + rng.normal(0, 2.2, n)), 4, 22)
exper = np.clip(np.round(rng.uniform(0, 35, n)), 0, 40)
mulher = rng.binomial(1, 0.48, n)
lsal = (1.2 + 0.08 * educ + 0.03 * exper - 0.0005 * exper**2 - 0.15 * mulher
        + 0.10 * habilidade + rng.normal(0, 0.35, n))
salvar(pd.DataFrame({"id": range(1, n + 1), "salario_hora": np.exp(lsal).round(2),
                     "educ": educ.astype(int), "exper": exper.astype(int),
                     "mulher": mulher, "habilidade": habilidade.round(3)}),
       "04-regressao-multipla", "salarios.csv")

# ---------------------------------------------------------------------------
# Conteúdo 5 — painel de empresas (efeitos fixos)
# ROA = 0,5·tamanho − 0,10·alavancagem + a_i + λ_t + u ; a_i (qualidade da
# gestão, não observada) é NEGATIVAMENTE correlacionada com a alavancagem.
# ---------------------------------------------------------------------------
N, T = 150, 6
ids = np.repeat(np.arange(1, N + 1), T)
anos = np.tile(np.arange(2018, 2018 + T), N)
a_i = rng.normal(0, 3, N)
alav_media = 45 - 4.0 * a_i + rng.normal(0, 6, N)
alav = np.repeat(alav_media, T) + rng.normal(0, 6, N * T)
tam = np.repeat(rng.normal(8, 1.2, N), T) + rng.normal(0, 0.3, N * T)
lam = np.tile(np.array([0.0, 0.4, -1.5, 0.8, 1.0, 0.6]), N)          # choques anuais
roa = 2 + 0.5 * tam - 0.10 * alav + np.repeat(a_i, T) + lam + rng.normal(0, 1.5, N * T)
salvar(pd.DataFrame({"empresa": ids, "ano": anos, "roa": roa.round(3),
                     "alavancagem": alav.round(2), "tamanho": tam.round(3)}),
       "05-dados-em-painel", "painel_empresas.csv")

# ---------------------------------------------------------------------------
# Conteúdo 6 — diferenças em diferenças
# 100 municípios, 2010–2019; 40 adotam um programa em 2015.
# Efeito verdadeiro: +30 no gasto per capita, crescendo 5 por ano após adoção.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(7)          # semente própria deste bloco
N, anos_did = 100, np.arange(2010, 2020)
tratado = (np.arange(N) < 40).astype(int)
fe = rng.normal(0, 25, N) + 40 * tratado                            # nível diferente é permitido
linhas = []
for i in range(N):
    for t in anos_did:
        pos = int(t >= 2015)
        efeito = (30 + 5 * (t - 2015)) * tratado[i] * pos
        y = 300 + fe[i] + 8 * (t - 2010) + efeito + rng.normal(0, 12)
        linhas.append((i + 1, t, tratado[i], pos, round(y, 2)))
salvar(pd.DataFrame(linhas, columns=["municipio", "ano", "tratado", "pos", "gasto_saude_pc"]),
       "06-diferencas-em-diferencas", "programa_saude.csv")

# ---------------------------------------------------------------------------
# Conteúdo 7 — RDD fuzzy: programa fictício de crédito subsidiado
# Empresas com pontuação >= 60 (escala 30–90) podem obter o crédito; nem todas
# contratam e algumas abaixo do corte conseguem por recurso administrativo.
# Efeito verdadeiro do crédito sobre o investimento: +R$ 35 mil.
# ---------------------------------------------------------------------------
rng = np.random.default_rng(6060)
n = 2500
pontuacao = rng.uniform(30, 90, n).round(1)
acima = (pontuacao >= 60).astype(int)
credito = rng.binomial(1, np.where(acima == 1, 0.80, 0.10))
z = (pontuacao - 60) / 10
investimento = 120 + 8 * z + 1.0 * z**2 + 35 * credito + rng.normal(0, 30, n)
salvar(pd.DataFrame({"empresa": range(1, n + 1), "pontuacao": pontuacao,
                     "acima_corte": acima, "credito": credito,
                     "investimento": investimento.round(2)}),
       "07-regressao-descontinua", "rdd_credito.csv")

# ---------------------------------------------------------------------------
# Conteúdo 8 — controle sintético
# 1 estado tratado + 15 doadores, 2000–2019; política em 2012.
# Modelo de fatores; o tratado é ~ combinação de 3 doadores. Efeito: −2 por
# ano a partir de 2012 (acumulando até −16).
# ---------------------------------------------------------------------------
rng = np.random.default_rng(2012)
J, anos_sc = 16, np.arange(2000, 2020)
f1 = np.linspace(0, 1, len(anos_sc)) ** 1.3 * 30
f2 = np.sin(np.linspace(0, 3 * np.pi, len(anos_sc))) * 6
load1 = rng.uniform(0.4, 1.6, J)
load2 = rng.uniform(-1, 1, J)
nivel = rng.normal(100, 12, J)
w_verd = np.array([0, 0.5, 0, 0, 0.3, 0, 0, 0, 0, 0, 0, 0.2, 0, 0, 0])
nivel[0], load1[0], load2[0] = (w_verd @ nivel[1:], w_verd @ load1[1:], w_verd @ load2[1:])
Y = nivel[:, None] + load1[:, None] * f1 + load2[:, None] * f2 + rng.normal(0, 1.2, (J, len(anos_sc)))
efeito_sc = np.where(anos_sc >= 2012, -2.0 * (anos_sc - 2011), 0.0)
Y[0] += efeito_sc
linhas = [("Tratado" if j == 0 else f"Doador {j:02d}", int(t), int(j == 0), round(Y[j, k], 3))
          for j in range(J) for k, t in enumerate(anos_sc)]
salvar(pd.DataFrame(linhas, columns=["unidade", "ano", "tratado", "y"]),
       "08-controle-sintetico", "painel_sintetico.csv")
