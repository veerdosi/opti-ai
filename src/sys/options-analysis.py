import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Union, Tuple

@dataclass
class OptionContract:
    symbol: str
    strike: float
    expiry: datetime
    option_type: str  # 'call' or 'put'
    position: int     # positive for long, negative for short
    price: float
    
class OptionsStrategy:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.positions: List[OptionContract] = []
        
    def add_position(self, contract: OptionContract):
        self.positions.append(contract)
        
    def calculate_greeks(self, 
                        current_price: float, 
                        volatility: float, 
                        risk_free_rate: float) -> Dict[str, float]:
        """
        Calculate option Greeks for the entire strategy
        Returns dictionary with total delta, gamma, theta, vega
        """
        total_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        for position in self.positions:
            # Calculate time to expiry in years
            tte = (position.expiry - datetime.now()).days / 365
            
            # Basic Black-Scholes implementation for Greeks
            d1 = (np.log(current_price / position.strike) + 
                  (risk_free_rate + volatility**2/2) * tte) / (volatility * np.sqrt(tte))
            d2 = d1 - volatility * np.sqrt(tte)
            
            if position.option_type == 'call':
                delta = self._norm_cdf(d1)
                theta = (-current_price * volatility * np.exp(-d1**2/2) / 
                        (2 * np.sqrt(2*np.pi*tte)))
            else:  # put
                delta = self._norm_cdf(d1) - 1
                theta = (-current_price * volatility * np.exp(-d1**2/2) / 
                        (2 * np.sqrt(2*np.pi*tte)))
            
            gamma = np.exp(-d1**2/2) / (current_price * volatility * np.sqrt(2*np.pi*tte))
            vega = current_price * np.sqrt(tte) * np.exp(-d1**2/2) / np.sqrt(2*np.pi)
            
            # Adjust for position size and direction
            total_greeks['delta'] += delta * position.position
            total_greeks['gamma'] += gamma * position.position
            total_greeks['theta'] += theta * position.position
            total_greeks['vega'] += vega * position.position
            
        return total_greeks
    
    @staticmethod
    def _norm_cdf(x):
        return (1 + np.erf(x/np.sqrt(2))) / 2
    
    def calculate_pnl(self, current_prices: pd.Series) -> pd.Series:
        """
        Calculate P&L for the strategy across a range of prices
        Returns Series with P&L values
        """
        pnl = pd.Series(0, index=current_prices)
        
        for position in self.positions:
            if position.option_type == 'call':
                payoff = np.maximum(current_prices - position.strike, 0)
            else:  # put
                payoff = np.maximum(position.strike - current_prices, 0)
                
            pnl += (payoff - position.price) * position.position
            
        return pnl

class BacktestEngine:
    def __init__(self):
        self.strategies: Dict[str, OptionsStrategy] = {}
        self.results: Dict[str, pd.DataFrame] = {}
        
    def add_strategy(self, strategy: OptionsStrategy):
        self.strategies[strategy.name] = strategy
        
    def run_backtest(self, 
                    historical_data: pd.DataFrame,
                    volatility: float,
                    risk_free_rate: float) -> pd.DataFrame:
        """
        Run backtest for all registered strategies
        Returns DataFrame with performance metrics
        """
        results = []
        
        for strategy_name, strategy in self.strategies.items():
            # Calculate daily Greeks and P&L
            daily_metrics = []
            
            for date, row in historical_data.iterrows():
                greeks = strategy.calculate_greeks(
                    row['close'], 
                    volatility,
                    risk_free_rate
                )
                
                pnl = strategy.calculate_pnl(pd.Series([row['close']]))[0]
                
                metrics = {
                    'date': date,
                    'strategy': strategy_name,
                    'price': row['close'],
                    'pnl': pnl,
                    **greeks
                }
                daily_metrics.append(metrics)
            
            strategy_results = pd.DataFrame(daily_metrics)
            self.results[strategy_name] = strategy_results
            results.append(strategy_results)
            
        return pd.concat(results)

def create_credit_spread(
    symbol: str,
    expiry: datetime,
    long_strike: float,
    short_strike: float,
    is_call: bool,
    contracts_count: int = 1
) -> OptionsStrategy:
    """
    Create a credit spread strategy (bull put or bear call)
    """
    option_type = 'call' if is_call else 'put'
    strategy_type = 'Bear Call' if is_call else 'Bull Put'
    
    strategy = OptionsStrategy(
        name=f"{strategy_type} Spread {symbol}",
        description=f"{strategy_type} spread with long {long_strike} and short {short_strike}"
    )
    
    # Long position
    strategy.add_position(OptionContract(
        symbol=symbol,
        strike=long_strike,
        expiry=expiry,
        option_type=option_type,
        position=contracts_count,
        price=0  # To be filled with actual market data
    ))
    
    # Short position
    strategy.add_position(OptionContract(
        symbol=symbol,
        strike=short_strike,
        expiry=expiry,
        option_type=option_type,
        position=-contracts_count,
        price=0  # To be filled with actual market data
    ))
    
    return strategy