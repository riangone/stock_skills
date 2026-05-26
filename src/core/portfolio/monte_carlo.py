"""Monte Carlo simulation for portfolio growth (KIK-579).

Provides probabilistic projections using random sampling based on 
expected returns and annualized volatility.
"""

import numpy as np
from typing import Any, Dict, List, Optional, Tuple


def run_monte_carlo_simulation(
    current_value: float,
    mean_return: float,
    volatility: float,
    dividend_yield: float = 0.0,
    years: int = 10,
    monthly_add: float = 0.0,
    reinvest_dividends: bool = True,
    n_simulations: int = 1000,
) -> Dict[str, np.ndarray]:
    """Run Monte Carlo simulation for portfolio growth.

    Parameters
    ----------
    current_value : float
        Initial investment.
    mean_return : float
        Annualized expected mean return (e.g. 0.07).
    volatility : float
        Annualized standard deviation of returns (e.g. 0.15).
    dividend_yield : float
        Annualized dividend yield.
    years : int
        Simulation horizon in years.
    monthly_add : float
        Additional monthly contribution.
    reinvest_dividends : bool
        Whether to reinvest dividends.
    n_simulations : int
        Number of random paths to simulate.

    Returns
    -------
    dict
        Dictionary containing arrays for 'percentiles' and 'paths'.
    """
    # Convert annual to monthly for finer-grained simulation
    dt = 1/12
    n_periods = int(years * 12)
    
    # Pre-allocate array for results: (n_simulations, n_periods + 1)
    results = np.zeros((n_simulations, n_periods + 1))
    results[:, 0] = current_value
    
    # Generate random monthly returns using geometric Brownian motion assumption
    # Monthly mean = (1 + mean_return)**(1/12) - 1
    # Actually, simpler log-normal approximation:
    mu_monthly = (mean_return - 0.5 * volatility**2) * dt
    sigma_monthly = volatility * np.sqrt(dt)
    
    # Generate all random shocks at once
    shocks = np.random.normal(mu_monthly, sigma_monthly, (n_simulations, n_periods))
    
    # Iterate through months
    for t in range(1, n_periods + 1):
        # Capital gain from market movement
        prev_values = results[:, t-1]
        market_growth = np.exp(shocks[:, t-1])
        
        # Dividends (monthly rate)
        monthly_div_yield = dividend_yield / 12
        dividends = prev_values * monthly_div_yield
        
        if reinvest_dividends:
            results[:, t] = prev_values * market_growth + dividends + monthly_add
        else:
            results[:, t] = prev_values * market_growth + monthly_add
            
    # Calculate percentiles (10th, 50th, 90th)
    percentiles = {
        "p10": np.percentile(results, 10, axis=0),
        "p50": np.percentile(results, 50, axis=0),
        "p90": np.percentile(results, 90, axis=0),
    }
    
    return {
        "all_paths": results,
        "percentiles": percentiles
    }


def get_monte_carlo_summary(
    mc_results: Dict[str, Any]
) -> Dict[str, float]:
    """Extract key metrics from Monte Carlo results."""
    final_values = mc_results["all_paths"][:, -1]
    return {
        "median_final": float(np.median(final_values)),
        "p10_final": float(np.percentile(final_values, 10)),
        "p90_final": float(np.percentile(final_values, 90)),
        "prob_loss": float(np.mean(final_values < mc_results["all_paths"][0, 0])),
    }
