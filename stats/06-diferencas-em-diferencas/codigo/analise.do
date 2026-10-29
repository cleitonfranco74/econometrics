* Conteúdo 6 — Diferenças em diferenças (Estatística e Econometria, PROFINIT)
* Execute a partir desta pasta (codigo/).

import delimited "../dados/programa_saude.csv", clear
xtset municipio ano

regress gasto_saude_pc i.tratado##i.pos, vce(cluster municipio)
generate D = tratado * pos
reghdfe gasto_saude_pc D, absorb(municipio ano) vce(cluster municipio)

* Comando nativo (Stata 17+)
didregress (gasto_saude_pc) (D), group(municipio) time(ano)
estat trendplots
estat ptrends

* Estudo de eventos (2014 = referência)
reghdfe gasto_saude_pc ib2014.ano#1.tratado, absorb(municipio ano) vce(cluster municipio)
coefplot, keep(*.ano#1.tratado) vertical yline(0)
testparm 2010.ano#1.tratado 2011.ano#1.tratado 2012.ano#1.tratado 2013.ano#1.tratado

* Adoção escalonada: ssc install csdid
* generate g = cond(tratado == 1, 2015, 0)
* csdid gasto_saude_pc, ivar(municipio) time(ano) gvar(g)
* estat event
