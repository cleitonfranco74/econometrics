* Conteúdo 5 — Dados em painel (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

import delimited "../dados/painel_empresas.csv", clear
xtset empresa ano
xtdescribe
xtsum roa alavancagem tamanho          // variação overall, between e within

regress roa alavancagem tamanho i.ano, vce(cluster empresa)       // pooled
xtreg roa alavancagem tamanho i.ano, fe vce(cluster empresa)      // efeitos fixos
estimates store fe
xtreg roa alavancagem tamanho i.ano, re vce(cluster empresa)      // efeitos aleatórios
regress D.roa D.alavancagem D.tamanho i.ano, vce(cluster empresa) // primeiras diferenças

* Hausman (exige erros convencionais)
quietly xtreg roa alavancagem tamanho i.ano, fe
estimates store fe_c
quietly xtreg roa alavancagem tamanho i.ano, re
hausman fe_c .

* Com muitos efeitos fixos: ssc install reghdfe
reghdfe roa alavancagem tamanho, absorb(empresa ano) vce(cluster empresa)
