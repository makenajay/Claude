# =====================================================================
#  ANOVA from First Principles — R companion script
#  Run it top to bottom (Ctrl+Shift+Enter in RStudio). Every number
#  printed here matches a number in the chapter.
#  Packages used later: car, lme4, survey  ->  install.packages(c("car","lme4","survey"))
# =====================================================================

# ---- 1. Variance by hand ---------------------------------------------
y <- c(8, 10, 12)
SST <- sum((y - mean(y))^2)          # 8
SST / (length(y) - 1)                # sample variance = 4
var(y)                               # R's built-in agrees

# ---- 2. One-way ANOVA: fertilizer and wheat yield ------------------------
fert <- data.frame(
  type  = factor(rep(c("A", "B", "C"), each = 5)),
  yield = c(18, 20, 19, 21, 22,  23, 25, 24, 26, 25,  20, 21, 22, 19, 20)
)

# 2a. The decomposition, built from first principles
grand  <- mean(fert$yield)
gmeans <- ave(fert$yield, fert$type)            # each row's group mean
SST <- sum((fert$yield - grand)^2)              # 85.33
SSB <- sum((gmeans     - grand)^2)              # 64.93
SSW <- sum((fert$yield - gmeans)^2)             # 20.40
c(SST = SST, SSB_plus_SSW = SSB + SSW)          # identical

k <- nlevels(fert$type); n <- nrow(fert)
F <- (SSB / (k - 1)) / (SSW / (n - k))          # 19.10
pf(F, k - 1, n - k, lower.tail = FALSE)         # p = 0.00019

# 2b. The same thing in one line
fit <- aov(yield ~ type, data = fert)
summary(fit)

# 2c. Effect sizes
eta2   <- SSB / SST                                      # 0.761
MSW    <- SSW / (n - k)
omega2 <- (SSB - (k - 1) * MSW) / (SST + MSW)            # 0.707 (less biased)
round(c(eta2 = eta2, omega2 = omega2), 3)

# 2d. Which pairs differ?  Tukey's honest significant difference
TukeyHSD(fit)
plot(TukeyHSD(fit), las = 1)

# 2e. Diagnostics
par(mfrow = c(1, 2)); plot(fit, which = 1:2); par(mfrow = c(1, 1))

# ---- 3. When spreads differ: Welch's ANOVA --------------------------------
courier <- data.frame(
  firm  = factor(rep(c("Fast", "Budget", "Local"), each = 5)),
  hours = c(30, 31, 29, 30, 31,  26, 44, 33, 24, 47,  34, 36, 35, 37, 34)
)
tapply(courier$hours, courier$firm, var)          # Budget 107.7 vs Fast 0.7 vs Local 1.7 !
summary(aov(hours ~ firm, data = courier))        # classical: F = 1.05, p = 0.38
oneway.test(hours ~ firm, data = courier)         # Welch:     F = 23.9, p = 0.0009

# ---- 4. Regression is ANOVA too: farm yield ---------------------------------
farm <- data.frame(
  size  = c(5, 8, 10, 12, 15, 18, 20, 24, 28, 32, 35, 40),
  fert  = c(35, 45, 50, 55, 65, 70, 75, 85, 92, 100, 105, 115),
  yield = c(21.58, 21.22, 22.45, 22.08, 24.22, 24.35, 25.78, 25.52, 27.08, 27.10, 28.72, 29.28)
)
m1 <- lm(yield ~ size + fert, data = farm)
summary(m1)                    # overall F = 114, R^2 = 0.962 ... but each slope p ~ 0.51
anova(lm(yield ~ 1, data = farm), m1)   # the regression F test IS an ANOVA comparison
cor(farm$size, farm$fert)      # 0.996  -> collinearity
car::vif(m1)                   # VIF ~ 123 (rule of thumb: worry above 5-10)

# ---- 5. Two-way ANOVA with interaction -------------------------------------
cells <- expand.grid(rep = 1:3, irrigation = c("Low", "Medium", "High"),
                     variety = c("V1", "V2", "V3"))
cells$irrigation <- factor(cells$irrigation, levels = c("Low", "Medium", "High"))
cell_mean <- c(28, 31, 33,   27, 33, 39,   33, 33, 32)   # V1, V2, V3 rows (interaction data)
cells$yield <- rep(cell_mean, each = 3) + c(-1, 0, 1)
summary(aov(yield ~ variety * irrigation, data = cells))
with(cells, interaction.plot(irrigation, variety, yield, lwd = 2, col = c("#2a78d6", "#eb6834", "#1baf7a")))

# ---- 6. ICC and design effect from a one-way random-effects ANOVA -------------
psu_means <- c(42, 47, 51, 55, 60, 64, 68, 73)
svy <- data.frame(psu   = factor(rep(1:8, each = 5)),
                  score = rep(psu_means, each = 5) + c(-2, -1, 0, 1, 2))
tab <- summary(aov(score ~ psu, data = svy))[[1]]
MSB <- tab$`Mean Sq`[1]; MSW <- tab$`Mean Sq`[2]; m <- 5
sigma2_b <- max((MSB - MSW) / m, 0)                      # 113.5
icc  <- sigma2_b / (sigma2_b + MSW)                      # 0.978
deff <- 1 + (m - 1) * icc                                # 4.91
c(icc = icc, deff = deff, n_eff = nrow(svy) / deff)      # n_eff ~ 8

# Same ICC from a mixed model (lme4)
library(lme4)
mm <- lmer(score ~ 1 + (1 | psu), data = svy)
vc <- as.data.frame(VarCorr(mm))$vcov
vc[1] / sum(vc)                                          # 0.978 again

# ---- 7. Design-based analysis with the survey package ------------------------
library(survey)
set.seed(2026)
booths <- 200; m <- 12
pun <- data.frame(booth = rep(1:booths, each = m))
booth_effect <- rep(rnorm(booths, 0, 0.55), each = m)    # creates clustering
pun$vote_A <- rbinom(nrow(pun), 1, plogis(-0.62 + booth_effect))
pun$wt <- 1                                              # equal weights for the demo
des <- svydesign(ids = ~booth, weights = ~wt, data = pun)
svymean(~vote_A, des, deff = "replace")                  # estimate, SE and DEFF
confint(svymean(~vote_A, des))

# ---- 8. Planning helpers ---------------------------------------------------
deff_equal   <- function(m, rho) 1 + (m - 1) * rho
deff_unequal <- function(mbar, cv, rho) 1 + ((1 + cv^2) * mbar - 1) * rho
moe          <- function(p, n, deff = 1) 1.96 * sqrt(deff * p * (1 - p) / n)
m_opt        <- function(c_cluster, c_person, rho) sqrt(c_cluster / c_person * (1 - rho) / rho)

deff_equal(12, 0.06)                   # 1.66
moe(0.35, 2400)                        # +/- 1.9 points under SRS
moe(0.35, 2400, deff = 1.66)           # +/- 2.5 points with booth clustering
m_opt(6000, 300, 0.06)                 # about 18 interviews per booth
