# %%
# %%

from data.data_request import Token, Token_Pair
from analysis.analysis import Analysis
from simulation.simulation import Simulation
import pandas as pd
import numpy as np

lksm_usd = Token_Pair(Token("liquid-ksm", "LKSM"), Token("dollar", "USD"))
ksm_usd = Token_Pair(Token("kusama", "KSM"), Token("dollar", "USD"))

lksm_usd.get_prices()
lksm_usd.calculate_returns()

ksm_usd.get_prices()
ksm_usd.calculate_returns()

# Analysis of the variance and correlation of LKSM/KSM
print(
    f"The annualized volatility of LKSM for the period from {lksm_usd.returns.index[0]} \
    until {lksm_usd.returns.index[-1]} is {round(lksm_usd.returns.std()[0]*365**0.5,4)*100}%"
)

print(
    f"The annualized volatility of KSM for the period from {ksm_usd.returns.index[0]} \
    until {ksm_usd.returns.index[-1]} is {round(ksm_usd.returns.std()[0]*365**0.5,4)*100}% \n"
)

returns = pd.concat([lksm_usd.returns, ksm_usd.returns], axis=1).dropna()
returns.columns = ["LKSM Returns", "KSM Returns"]
corr = returns.corr()["LKSM Returns"]["KSM Returns"]
print(f"The correlation between LKSM and KSM is {round(corr,3)}")
print(
    f"The part of the variance unexplained by linear correlation between LKSM and KSM is {round((corr**2-1)*100,1)}%)"
)

# %%
# Based on the above comparison of LKSM and KSM, we're using KSM as a proxy for LKSM for
# the rest of this analysis, with the exception of the liquidity, for which we'll be using LKSM.
#
# BTC is the debt in the system and if BTC increases in price, the over-collateralization ratio drops
# Vice versa, if the price of KSM decreases, the collateralization ratio drops.
#
# To model this, we get the inverse of the KSM/BTC price to have BTC as base currency.
# We then select the n-th worst trajectories of the inverse price.

quote_currency = Token("bitcoin", "BTC")
base_currency = Token("kusama", "KSM")

pair = Token_Pair(base_currency, quote_currency)
pair.get_prices(start_date="2019-09-20", inverse=True)
pair.calculate_returns()
pair.prices.plot()

# the std scaled by the square-root of time, 365 days to annulize it, **0.5 to square it
print(f"BTC/KSM had an annualized std of {pair.returns.std()[0] *365**0.5}")
print(f"BTC/KSM had an annualized mean return of {pair.calculate_mean_return()}")
print(
    f"BTC/KSM had a total return of {pair.prices.iloc[-1,0] / pair.prices.iloc[0,0] -1}"
)

# %%


# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 10 days and 24 hours each
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(pair, strategy="GBM")
sim.simulate(
    steps=24,
    maturity=7,
    n_simulations=10_000,
    initial_value=1,
    sigma=pair.returns.std()[0],
    mu=0,
)


# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below 1 only with a 0.1% chance in 10 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
liquidation_threshold_margin = simple_analysis.get_threshold_multiplier(
    alpha=0.999
)  # <- this can be changed ofc
premium_redeem_threshold_margin = simple_analysis.get_threshold_multiplier(
    alpha=0.90
)  # <- this can be changed ofc

print(
    f"The estimated liquidation threshold is ~{int(liquidation_threshold_margin * 100)}% of the debt value"
)
print(
    f"The estimated premium redeem threshold is ~{int(liquidation_threshold_margin * premium_redeem_threshold_margin * 100)}% of the debt value"
)

# %%
# Initialize and run the simulation: Each path represents the price change of the collateral/debt
# We simulate 10,000 trajectories with a duration of 10 days and 24 hours each
# and assume a normal distribution (GBM) with the mean and std of bitcoin over the past 5 years
sim = Simulation(pair, strategy="GBM")
sim.simulate(
    steps=24,
    maturity=21,
    n_simulations=10_000,
    initial_value=1,
    sigma=pair.returns.std()[0],
    mu=0,
)

# Analize the results
# Initialize the analysis
simple_analysis = Analysis(sim)

# This gives us the secure threshold multiplier, stating that:
# The collateral/debt ratio will fall below the liquidation_threshold_margin with a 10% chance in 21 days or...
# This assumes no premium redeem, additional collateralization or liquidation.
secure_threshold_margin = simple_analysis.get_threshold_multiplier(
    alpha=0.90
)  # <- this can be changed ofc

print(
    f"The estimated secure threshold is ~{int(liquidation_threshold_margin * secure_threshold_margin * 100)}% of the debt value"
)

# %%