# Conteúdo 8 — Estudo de caso didático: teto de gastos (EC 95/2016) com SDID
# Synthetic Difference-in-Differences (Arkhangelsky, Athey, Hirshberg, Imbens & Wager, 2021, AER).
# Base SIMULADA em ../../dados_caso/teto_gastos_sintetica.csv. Requer: pip install pandas numpy scipy
#
# Implementação didática do estimador para uma unidade tratada (o Brasil), comparada com
# DiD e controle sintético (SC). Em pesquisa, use o pacote synthdid (R) ou sdid (Stata).
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

AQUI = Path(__file__).resolve().parent
df = pd.read_csv(AQUI.parents[1] / "dados_caso" / "teto_gastos_sintetica.csv")
ANOS = np.array(sorted(df["ano"].unique()))
PRE = ANOS <= 2016                      # teto aprovado em dez/2016; efeito a partir de 2017
POS = ANOS >= 2017


def simplex_ls(A, b, zeta2=0.0, intercepto=True):
    """min ||c + A w − b||² + zeta2·||w||²  com w ≥ 0, Σw = 1 (c livre se intercepto=True)."""
    k = A.shape[1]
    def obj(v):
        c, w = (v[0], v[1:]) if intercepto else (0.0, v)
        r = c + A @ w - b
        return r @ r + zeta2 * (w @ w)
    x0 = np.r_[[0.0] if intercepto else [], np.full(k, 1 / k)]
    bnd = ([(None, None)] if intercepto else []) + [(0, 1)] * k
    cons = [{"type": "eq", "fun": (lambda v: v[1:].sum() - 1) if intercepto else (lambda v: v.sum() - 1)}]
    v = minimize(obj, x0, method="SLSQP", bounds=bnd, constraints=cons, options={"ftol": 1e-12, "maxiter": 3000}).x
    return (v[0], v[1:]) if intercepto else (0.0, v)


def estimar(Y, tratado, metodo, PRE=PRE, POS=POS):
    """Y: DataFrame anos x países. Retorna efeito τ, pesos de unidades ω, pesos de tempo λ e trajetórias."""
    doad = [c for c in Y.columns if c != tratado]
    Y0, y1 = Y[doad].values, Y[tratado].values          # T x N0 e T
    T0, N0 = PRE.sum(), len(doad)
    pos = POS
    if metodo == "DiD":
        w, lam = np.full(N0, 1 / N0), np.full(T0, 1 / T0)
    elif metodo == "SC":
        _, w = simplex_ls(Y0[PRE], y1[PRE], intercepto=False)
        lam = np.zeros(T0)                               # SC não usa período de referência
    else:                                                # SDID
        dif = np.diff(Y0[PRE], axis=0)
        zeta = (1 * pos.sum()) ** 0.25 * dif.std(ddof=1)
        _, w = simplex_ls(Y0[PRE], y1[PRE], zeta2=zeta**2 * T0)
        _, lam = simplex_ls(Y0[PRE].T, Y0[pos].mean(axis=0), zeta2=(1e-6 * dif.std(ddof=1))**2 * N0)
    controle = Y0 @ w
    ref = lam @ (y1[PRE] - controle[PRE]) if metodo != "SC" else 0.0   # diferença de nível do período de referência
    contraf = controle + ref
    tau = float((y1[pos] - contraf[pos]).mean())
    return {"tau": tau, "w": dict(zip(doad, w)), "lam": lam, "contrafactual": contraf, "efeito": y1 - contraf}


saida = {"anos": ANOS.tolist()}
JANELAS = {"completa": ANOS <= 2016,            # pré-tratamento 2000–2016
           "sem_2014_2016": ANOS <= 2013}       # exclui a recessão própria do Brasil (2014–2016)
for var, rot, col_ef in [("juro_real_10a", "Juro real de 10 anos (%)", "efeito_verdadeiro_juro"),
                         ("resultado_primario", "Resultado primário (% do PIB)", "efeito_verdadeiro_primario")]:
    Y = df.pivot(index="ano", columns="pais", values=var)
    verd = df[df.pais == "Brasil"].set_index("ano")[col_ef].values
    out = {"rotulo": rot, "brasil": Y["Brasil"].round(3).tolist(), "verdadeiro": verd.tolist(),
           "verdadeiro_medio": round(float(verd[POS].mean()), 3)}
    print(f"\n== {rot}  (efeito verdadeiro médio 2017–2019 = {verd[POS].mean():+.2f})")
    for janela, pre in JANELAS.items():
        print(f"  -- janela pré-tratamento: {'2000–2016' if janela == 'completa' else '2000–2013'}")
        out[janela] = {}
        for m in ["DiD", "SC", "SDID"]:
            r = estimar(Y, "Brasil", m, PRE=pre)
            # Inferência por placebos: cada doador vira “tratado”, sem o Brasil no grupo de controle
            plac = {p: estimar(Y.drop(columns=["Brasil"]), p, m, PRE=pre)["tau"] for p in Y.columns if p != "Brasil"}
            ep = float(np.std(list(plac.values()), ddof=1))
            p_val = (1 + sum(abs(v) >= abs(r["tau"]) for v in plac.values())) / (1 + len(plac))
            rmspe_pre = float(np.sqrt(np.mean(r["efeito"][pre] ** 2)))
            out[janela][m] = {
                "tau": round(r["tau"], 3), "ep": round(ep, 3), "p": round(p_val, 4), "rmspe_pre": round(rmspe_pre, 3),
                "pesos": {k: round(float(v), 3) for k, v in sorted(r["w"].items(), key=lambda x: -x[1]) if v > 0.005},
                "lambda": {int(a): round(float(l), 3) for a, l in zip(ANOS[pre], r["lam"]) if l > 0.005},
                "contrafactual": np.round(r["contrafactual"], 3).tolist(), "efeito": np.round(r["efeito"], 3).tolist(),
                "placebos": {k: round(v, 3) for k, v in plac.items()}}
            print(f"     {m:4s} τ = {r['tau']:+.3f}  (ep placebo {ep:.3f}; p = {p_val:.3f})  RMSPE pré {rmspe_pre:.3f}"
                  + (f"  λ: {out[janela][m]['lambda']}" if m == "SDID" else ""))
    saida[var] = out
(AQUI / "teto_gastos_sdid_resultados.json").write_text(json.dumps(saida, ensure_ascii=False))
