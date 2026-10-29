# Conteúdo 3 — Correlação, causalidade e regressão simples (Estatística e Econometria, PROFINIT)
# Execute a partir desta pasta (codigo/).

df <- read.csv("../dados/publicidade_vendas.csv")
cor(df[, c("vendas", "publicidade", "tamanho")])
cor(df$vendas, df$publicidade, method = "spearman")
cor.test(df$vendas, df$publicidade)

m1 <- lm(vendas ~ publicidade, data = df)
summary(m1)
cov(df$publicidade, df$vendas) / var(df$publicidade)   # b1 à mão

# Erros-padrão robustos
library(fixest)
feols(vendas ~ publicidade, data = df, vcov = "hetero")

predict(m1, newdata = data.frame(publicidade = 15))
plot(df$publicidade, df$vendas); abline(m1, col = "red")

summary(lm(vendas ~ publicidade + tamanho, data = df))
