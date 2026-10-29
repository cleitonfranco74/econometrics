* Conteúdo 4 — Regressão linear múltipla (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

import delimited "../dados/salarios.csv", clear
generate lsal = ln(salario_hora)

regress lsal educ, robust
estimates store m1
regress lsal educ c.exper##c.exper i.mulher, robust
estimates store m2
test exper c.exper#c.exper              // teste F conjunto
margins, dydx(exper) at(exper = 10)     // efeito marginal aos 10 anos
regress lsal educ c.exper##c.exper i.mulher habilidade, robust
estimates store m3
estimates table m1 m2 m3, b(%9.4f) se stats(N r2 r2_a)

* Viés de variável omitida
quietly regress habilidade educ c.exper##c.exper i.mulher
display _b[educ]

* Interação
regress lsal c.educ##i.mulher c.exper##c.exper, robust

* VIF
quietly regress lsal educ exper mulher
estat vif
