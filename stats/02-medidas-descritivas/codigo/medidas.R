# Medidas descritivas em R — Estatística (PROFINIT), Conteúdo 2
df <- read.csv("../dados/retornos_mensais.csv")
a  <- df$acao_A

# Tendência central
mean(a); median(a)
moda <- function(x) { t <- table(x); as.numeric(names(t)[t == max(t)]) }
moda(a)
mean(a, trim = 0.10)                         # média aparada 10%
(prod(1 + a / 100)^(1 / length(a)) - 1) * 100  # média geométrica

# Separatrizes (type = 7 é o padrão)
q <- quantile(a, c(0.25, 0.75)); iqr <- IQR(a)
c(q[1] - 1.5 * iqr, q[2] + 1.5 * iqr)        # cercas de Tukey

# Dispersão (var e sd já usam n − 1)
var(a); sd(a); sd(a) / mean(a); sd(a) * sqrt(12)

# Forma: estimadores ajustados (iguais ao Excel)
assimetria <- function(x) {
  n <- length(x); z <- (x - mean(x)) / sd(x)
  n / ((n - 1) * (n - 2)) * sum(z^3)
}
curtose_excesso <- function(x) {
  n <- length(x); z <- (x - mean(x)) / sd(x)
  n * (n + 1) / ((n - 1) * (n - 2) * (n - 3)) * sum(z^4) -
    3 * (n - 1)^2 / ((n - 2) * (n - 3))
}
assimetria(a); curtose_excesso(a)

# Associação
cov(df$acao_A, df$acao_B); cor(df$acao_A, df$acao_B)

summary(df[, c("acao_A", "acao_B")])
boxplot(df[, c("acao_A", "acao_B")], main = "Retornos mensais (%)")
