"""Gera as pequenas bases dos exemplos clássicos de correlação usados em aula.

- sorvete_afogamentos.csv: série mensal ILUSTRATIVA (simulada) de uma cidade litorânea,
  em que a temperatura afeta vendas de sorvete e afogamentos.
- nicolas_cage_afogamentos.csv: correlação espúria divulgada por Tyler Vigen
  (tylervigen.com/spurious-correlations).

As bases sorvete_afogamentos_aula.csv, margarina_divorcio_maine.csv,
carga_tributaria_gini.csv, salario_minimo_cesta_basica.csv e vacinacao_obitos.csv
vêm das planilhas da disciplina e não são geradas aqui.
- gasto_saude_suicidio_ocde.csv: valores aproximados do gráfico dos slides
  (gasto: Peterson-KFF Health System Tracker 2024; suicídio: OECD Health Statistics).
"""
from pathlib import Path

import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent

# Sorvete e afogamentos (2022–2024, mensal). Temperatura é o confundidor.
rng = np.random.default_rng(7)
base = np.array([30.5, 30.8, 29.5, 27.0, 24.2, 22.0, 21.8, 22.9, 24.0, 25.8, 27.4, 29.4])
temp = np.round(np.tile(base, 3) + rng.normal(0, 0.8, 36), 1)
sorvete = np.round(20 + 3.2 * (temp - 22) + rng.normal(0, 2.2, 36), 1)
afog = np.round(4 + 0.75 * (temp - 22) + rng.normal(0, 0.9, 36)).clip(0).astype(int)
meses = pd.period_range("2022-01", periods=36, freq="M").astype(str)
pd.DataFrame({"mes": meses, "temperatura_media_c": temp, "sorvetes_mil_unid": sorvete,
              "afogamentos": afog}).to_csv(AQUI / "sorvete_afogamentos.csv", index=False)

pd.DataFrame({"ano": range(1999, 2010),
              "afogamentos_em_piscina_eua": [109, 102, 102, 98, 85, 95, 96, 98, 123, 94, 102],
              "filmes_nicolas_cage": [2, 2, 2, 3, 1, 1, 2, 3, 4, 1, 4]}
             ).to_csv(AQUI / "nicolas_cage_afogamentos.csv", index=False)

pd.DataFrame({
    "pais": ["Japão", "Bélgica", "França", "Suécia", "Áustria", "Austrália", "Canadá",
             "Países Baixos", "Alemanha", "Suíça", "Reino Unido", "Estados Unidos"],
    "gasto_saude_pc_usd_ppp": [5500, 7200, 6900, 7300, 8500, 6500, 7000, 7800, 9000, 9700, 6300, 14800],
    "suicidio_por_100mil": [15.7, 15.3, 12.9, 12.4, 13.0, 11.3, 10.9, 9.9, 9.7, 9.7, 6.9, 14.1],
}).to_csv(AQUI / "gasto_saude_suicidio_ocde.csv", index=False)

if __name__ == "__main__":
    import statsmodels.formula.api as smf
    s = pd.read_csv(AQUI / "sorvete_afogamentos.csv")
    rx = smf.ols("sorvetes_mil_unid ~ temperatura_media_c", s).fit().resid
    ry = smf.ols("afogamentos ~ temperatura_media_c", s).fit().resid
    print("sorvete x afogamentos r =", round(s.sorvetes_mil_unid.corr(s.afogamentos), 3),
          " parcial (controlando temperatura) =", round(np.corrcoef(rx, ry)[0, 1], 3))
    print(smf.ols("afogamentos ~ sorvetes_mil_unid", s).fit().params.round(3).to_dict())
    print(smf.ols("afogamentos ~ sorvetes_mil_unid + temperatura_media_c", s).fit().summary().tables[1])
