"""Gera as pequenas bases dos exemplos clássicos de correlação usados em aula.

- sorvete_afogamentos.csv: série mensal ILUSTRATIVA (simulada) de uma cidade litorânea,
  em que a temperatura afeta vendas de sorvete e afogamentos.
- carga_tributaria_gini.csv: valores APROXIMADOS lidos do gráfico “Carga tributária ×
  concentração de renda” dos slides da disciplina.
- margarina_divorcio_maine.csv e nicolas_cage_afogamentos.csv: correlações espúrias
  divulgadas por Tyler Vigen (tylervigen.com/spurious-correlations).
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

pd.DataFrame({
    "pais": ["Brasil", "México", "Chile", "Peru", "Equador", "EUA", "Reino Unido", "Austrália",
             "Canadá", "Noruega", "Dinamarca", "Espanha", "Suécia", "Alemanha", "Índia", "Holanda", "Bélgica"],
    "gini": [0.570, 0.550, 0.494, 0.446, 0.426, 0.376, 0.373, 0.339, 0.329, 0.326, 0.321, 0.323,
             0.312, 0.311, 0.301, 0.286, 0.283],
    "carga_tributaria_pib": [36.7, 18.8, 22.6, 16.2, 19.8, 31.3, 38.9, 32.2, 39.4, 44.0, 53.0, 37.3,
                             54.3, 39.9, 19.2, 42.5, 47.6],
}).to_csv(AQUI / "carga_tributaria_gini.csv", index=False)

pd.DataFrame({"ano": range(2000, 2010),
              "margarina_lb_per_capita_eua": [8.2, 7.0, 6.5, 5.3, 5.2, 4.0, 4.6, 4.5, 4.2, 3.7],
              "divorcios_por_mil_maine": [5.0, 4.7, 4.6, 4.4, 4.3, 4.1, 4.2, 4.2, 4.2, 4.1]}
             ).to_csv(AQUI / "margarina_divorcio_maine.csv", index=False)

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
