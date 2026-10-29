* Conteúdo 7 — Regressão descontínua (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

* ssc install rdrobust ; net install rddensity, from(https://raw.githubusercontent.com/rdpackages/rddensity/master/stata) replace
import delimited "../dados/rdd_credito.csv", clear
generate z = (pontuacao - 60) / 10

rdplot investimento z, c(0)                                  // gráfico
rdrobust credito z, c(0)                            // 1º estágio
rdrobust investimento z, c(0)                                // forma reduzida
rdrobust investimento z, c(0) fuzzy(credito)           // LATE
rdrobust investimento z, c(0) fuzzy(credito) p(2) bwselect(msesum)
rdrobust investimento z, c(0) fuzzy(credito) kernel(epanechnikov)

rddensity z, c(0) plot                                    // manipulação
rdrobust investimento z if z < 0, c(-1)                    // placebo em 50 pontos

* MQ2E numa janela fixa
ivregress 2sls investimento z c.z#i.acima_corte (credito = i.acima_corte) ///
    if abs(z) <= 2, robust
