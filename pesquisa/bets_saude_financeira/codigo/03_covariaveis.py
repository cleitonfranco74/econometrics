"""
03 - Exposição pré-determinada (DigYouth, eq. 2) e covariáveis municipais.

  Censo 2022 (SIDRA 9514): população total, homens 18-35 e pessoas 18-35
       (idades 18, 19, 20-24, 25-29, 30-34, 35).
  Anatel: densidade de banda larga fixa (acessos por 100 domicílios), dez/2022
       (arquivo Densidade_Banda_Larga_Fixa.csv do pacote de dados abertos
        acessos_banda_larga_fixa.zip).
  IBGE: população estimada 2024 e 2025 (SIDRA 6579); 2023 interpolada entre
       Censo 2022 e 2024; PIB 2021 (SIDRA 5938, último ano anterior a 2023
       disponível para todos).

  DigYouth = (homens 18-35 / população 2022) x (banda larga por 100 domicílios)
  (o artigo usa "banda larga per capita"; a Anatel publica por domicílio —
   a ordenação entre municípios é praticamente a mesma)

Saídas: dados/processados/covariaveis_municipio.csv
        dados/processados/populacao_municipio_ano.csv
"""
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
ANATEL = RAIZ / "dados" / "brutos" / "anatel" / "bl.zip"
UFS = [11, 12, 13, 14, 15, 16, 17, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 32, 33,
       35, 41, 42, 43, 50, 51, 52, 53]


def sidra(caminho):
    for t in range(5):
        try:
            with urllib.request.urlopen("https://apisidra.ibge.gov.br/values" + caminho,
                                        timeout=300) as r:
                return pd.DataFrame(json.loads(r.read())[1:])
        except Exception:
            time.sleep(5 * (t + 1))
    raise RuntimeError(caminho)


# ---- Censo 2022: idade e sexo (por UF, para caber no limite do SIDRA) ----------
IDADES = "6575,6576,93087,93088,93089,6588,100362"     # 18,19,20-24,25-29,30-34,35,Total
partes = [sidra(f"/t/9514/n6/in%20n3%20{uf}/v/93/p/2022/c2/6794,4/c287/{IDADES}/c286/113635")
          for uf in UFS]
c = pd.concat(partes)
c["V"] = pd.to_numeric(c.V, errors="coerce")
c["cod_ibge"] = c.D1C.astype(int)
tot = c[(c.D4C == "6794") & (c.D5C == "100362")].set_index("cod_ibge").V
h1835 = c[(c.D4C == "4") & (c.D5C != "100362")].groupby("cod_ibge").V.sum()
p1835 = c[(c.D4C == "6794") & (c.D5C != "100362")].groupby("cod_ibge").V.sum()
nomes = c.drop_duplicates("cod_ibge").set_index("cod_ibge").D1N

# ---- Anatel: banda larga fixa por 100 domicílios, dez/2022 ----------------------
with zipfile.ZipFile(ANATEL) as z:
    den = pd.read_csv(z.open("Densidade_Banda_Larga_Fixa.csv"), sep=";", dtype=str,
                      encoding="utf-8-sig")
den = den[(den["Ano"] == "2022") & (den["Mês"] == "12")
          & (den["Nível Geográfico Densidade"].str.strip() == "Municipio")]
den = den.assign(cod_ibge=den["Código IBGE"].astype(int),
                 bl=pd.to_numeric(den.Densidade.str.replace(",", "."), errors="coerce"))
bl = den.set_index("cod_ibge").bl

# ---- População anual e PIB ------------------------------------------------------
pe = sidra("/t/6579/n6/all/v/9324/p/2024,2025")
pe = pe.assign(cod_ibge=pe.D1C.astype(int), ano=pe.D3N.astype(int),
               pop=pd.to_numeric(pe.V, errors="coerce"))
pop = pd.concat([pe[["cod_ibge", "ano", "pop"]],
                 pd.DataFrame({"cod_ibge": tot.index, "ano": 2022, "pop": tot.values})])
pop = pop.pivot(index="cod_ibge", columns="ano", values="pop")
pop[2023] = (pop[2022] + pop[2024]) / 2
pop = pop[[2022, 2023, 2024, 2025]]
pop.stack().rename("pop").reset_index().to_csv(PROC / "populacao_municipio_ano.csv", index=False)
pib = sidra("/t/5938/n6/all/v/37/p/2021")
pib = pib.assign(cod_ibge=pib.D1C.astype(int),
                 pib_mil=pd.to_numeric(pib.V, errors="coerce")).set_index("cod_ibge").pib_mil

cov = pd.DataFrame({"municipio": nomes, "pop_2022": tot, "homens_18_35": h1835,
                    "pessoas_18_35": p1835})
cov["sh_homens_18_35"] = cov.homens_18_35 / cov.pop_2022
cov["sh_jovens_18_35"] = cov.pessoas_18_35 / cov.pop_2022
cov["banda_larga_100dom"] = bl
cov["digyouth"] = cov.sh_homens_18_35 * cov.banda_larga_100dom
cov["pib_pc_2021"] = pib * 1000 / cov.pop_2022
cov["ln_pib_pc_2021"] = np.log(cov.pib_pc_2021)
cov["ln_pop_2022"] = np.log(cov.pop_2022)
cov["uf"] = cov.index // 100000
cov.index.name = "cod_ibge"
cov.reset_index().to_csv(PROC / "covariaveis_municipio.csv", index=False)
print(cov.shape)
print(cov.describe().T[["count", "mean", "min", "max"]].round(3).to_string())
