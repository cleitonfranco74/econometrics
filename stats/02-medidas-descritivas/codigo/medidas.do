* Medidas descritivas em Stata — Estatística (PROFINIT), Conteúdo 2
import delimited "../dados/retornos_mensais.csv", clear

* Resumo completo: média, dp, variância, percentis, assimetria e curtose
summarize acao_a acao_b, detail
* Atenção: no -summarize, detail- a assimetria e a curtose NÃO são ajustadas
* e a curtose não é "em excesso" (normal = 3). Os percentis usam a definição
* própria do Stata e podem diferir do Excel/R/Python em amostras pequenas.

tabstat acao_a acao_b, statistics(n mean median sd var cv min max iqr p25 p75) columns(statistics)

* Média geométrica dos retornos
generate double lr = ln(1 + acao_a/100)
quietly summarize lr
display "Média geométrica (%): " (exp(r(mean)) - 1)*100

* Volatilidade anualizada
quietly summarize acao_a
display "Volatilidade anual (%): " r(sd)*sqrt(12)

* Associação
correlate acao_a acao_b, covariance
correlate acao_a acao_b

graph box acao_a acao_b, title("Retornos mensais (%)")
