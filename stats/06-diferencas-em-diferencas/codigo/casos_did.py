# Conteúdo 6 — Estudos de caso de diferenças em diferenças com adoção escalonada
# Bases em ../../dados_caso/. Requer: pip install pandas numpy statsmodels
#
# Para cada caso estima:
#   (a) TWFE: y = efeito fixo da unidade + efeito fixo do ano + delta*D + u
#   (b) estudo de eventos TWFE (referência: ano anterior à adoção)
#   (c) Callaway & Sant'Anna (2021), implementação didática sem covariáveis,
#       com grupo de controle "nunca tratados" e erro-padrão por bootstrap
#       de unidades. Em pesquisa, use os pacotes csdid (Stata) ou did (R).
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

DADOS = Path(__file__).resolve().parents[2] / "dados_caso"


def twfe(df, y, d, i, t):
    m = smf.ols(f"{y} ~ {d} + C({i}) + C({t})", data=df).fit(
        cov_type="cluster", cov_kwds={"groups": df[i]})
    return m.params[d], m.bse[d]


def estudo_eventos_twfe(df, y, g, i, t, janela=(-5, 5)):
    """Dummies de tempo relativo à adoção (agrupando extremos), ref = -1."""
    d = df.copy()
    rel = np.where(d[g] > 0, d[t] - d[g], np.nan)
    rel = np.clip(rel, janela[0], janela[1])
    ks = [k for k in range(janela[0], janela[1] + 1) if k != -1]
    nomes = {}
    for k in ks:
        nome = f"ev_m{-k}" if k < 0 else f"ev_p{k}"
        d[nome] = (rel == k).astype(int)
        nomes[k] = nome
    m = smf.ols(f"{y} ~ {' + '.join(nomes.values())} + C({i}) + C({t})", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d[i]})
    return {k: (m.params[n], m.bse[n]) for k, n in nomes.items()}


def _att_gt(wide, grupos, anos, g_col):
    """ATT(g,t) com controles nunca tratados e base fixa g-1 (pré: base t-1)."""
    nunca = wide[grupos == 0]
    res = []
    for g in sorted(set(grupos) - {0}):
        if g - 1 not in anos:
            continue
        trat = wide[grupos == g]
        for t in anos:
            base = g - 1 if t >= g else t - 1
            if base not in anos or t == base:
                continue
            att = (trat[t] - trat[base]).mean() - (nunca[t] - nunca[base]).mean()
            res.append((g, t, t - g, att, len(trat)))
    return pd.DataFrame(res, columns=["g", "t", "e", "att", "n"])


def callaway_santanna(df, y, g, i, t, reps=199, semente=1, janela=(-5, 5)):
    wide = df.pivot(index=i, columns=t, values=y)
    grupos = df.groupby(i)[g].first().reindex(wide.index).values
    anos = list(wide.columns)

    def agrega(tab):
        tab = tab[(tab.e >= janela[0]) & (tab.e <= janela[1])]
        din = tab.groupby("e").apply(lambda x: np.average(x.att, weights=x.n), include_groups=False)
        pos = tab[tab.e >= 0]
        return din, np.average(pos.att, weights=pos.n)

    din, geral = agrega(_att_gt(wide, grupos, anos, g))
    rng = np.random.default_rng(semente)
    boots_d, boots_g = [], []
    idx = np.arange(len(wide))
    for _ in range(reps):
        s = rng.choice(idx, len(idx), replace=True)
        w = wide.iloc[s].reset_index(drop=True)
        try:
            bd, bg = agrega(_att_gt(w, grupos[s], anos, g))
        except ZeroDivisionError:
            continue
        boots_d.append(bd)
        boots_g.append(bg)
    se_d = pd.concat(boots_d, axis=1).std(axis=1)
    return {int(e): (din[e], se_d.get(e, np.nan)) for e in din.index}, (geral, np.std(boots_g, ddof=1))


CASOS = {
    "farmacia": dict(arquivo="farmacia_popular_mt.dta", y="mortes_hipertensao", d="fp",
                     g="ano_adocao", i="cod_mun", t="ano",
                     titulo="Farmácia Popular e mortes por hipertensão (MT, 2003–2011)"),
    "ifood": dict(arquivo="ifood_crime_sp.dta", y="lcrimes", d="post_ifood",
                  g="ifood_ano", i="cod_mun", t="ano",
                  titulo="iFood e crimes contra a propriedade (SP, 2010–2019), log"),
    "samu": dict(arquivo="samu_mt_2000_2020.dta", y="tx_mortes_transito", d="samu",
                 g="samu_ano", i="cod_mun", t="ano",
                 titulo="SAMU e mortes no trânsito por 100 mil hab. (MT, 2000–2020)"),
    "co2": dict(arquivo="co2_pd_2000_2020.dta", y="ln_co2_pc", d="pd",
                g="pd_ano", i="cod_pais", t="ano",
                titulo="Política de P&D e log das emissões de CO2 per capita (2000–2020)"),
}

if __name__ == "__main__":
    saida = {}
    for nome, c in CASOS.items():
        df = pd.read_stata(DADOS / c["arquivo"])
        if nome == "ifood":
            df["lcrimes"] = np.log(df["crimes"])
        b, se = twfe(df, c["y"], c["d"], c["i"], c["t"])
        es = estudo_eventos_twfe(df, c["y"], c["g"], c["i"], c["t"])
        cs_din, (cs_att, cs_se) = callaway_santanna(df, c["y"], c["g"], c["i"], c["t"])
        print(f"\n== {c['titulo']}")
        print(f"TWFE: {b:.4f} ({se:.4f})   CS (ATT geral): {cs_att:.4f} ({cs_se:.4f})")
        for k in sorted(es):
            cs = cs_din.get(k, (np.nan, np.nan))
            print(f"  e={k:+d}  TWFE {es[k][0]:8.4f} ({es[k][1]:.4f})   CS {cs[0]:8.4f} ({cs[1]:.4f})")
        saida[nome] = {"titulo": c["titulo"], "twfe": [b, se], "cs": [cs_att, cs_se],
                       "es_twfe": {k: list(v) for k, v in es.items()},
                       "es_cs": {k: list(v) for k, v in cs_din.items()}}
    (Path(__file__).resolve().parent / "casos_did_resultados.json").write_text(json.dumps(saida, indent=1))
