# quick_start.py

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf

class OptionsStrategy:
    def __init__(self, symbol, expiry, strikes, is_call):
        self.symbol = symbol
        self.expiry = expiry
        self.long_strike = strikes[0]
        self.short_strike = strikes[1]
        self.is_call = is_call
        self.position_type = "Bear Call" if is_call else "Bull Put"
        
    def calculate_greeks(self, current_price, volatility, risk_free_rate):
        """Calculate option Greeks using Black-Scholes"""
        # Time to expiry in years
        tte = (self.expiry - datetime.now()).days / 365
        
        def black_scholes_greeks(strike):
            d1 = (np.log(current_price/strike) + (risk_free_rate + volatility**2/2)*tte) / (volatility*np.sqrt(tte))
            d2 = d1 - volatility*np.sqrt(tte)
            
            # Calculate Greeks
            if self.is_call:
                delta = self._norm_cdf(d1)
            else:
                delta = self._norm_cdf(d1) - 1
                
            gamma = np.exp(-d1**2/2) / (current_price * volatility * np.sqrt(2*np.pi*tte))
            theta = -current_price * volatility * np.exp(-d1**2/2) / (2 * np.sqrt(2*np.pi*tte))
            vega = current_price * np.sqrt(tte) * np.exp(-d1**2/2) / np.sqrt(2*np.pi)
            
            return {'delta': delta, 'gamma': gamma, 'theta': theta, 'vega': vega}
        
        # Calculate Greeks for both options and combine
        long_greeks = black_scholes_greeks(self.long_strike)
        short_greeks = black_scholes_greeks(self.short_strike)
        
        # Net Greeks for the spread
        return {k: long_greeks[k] - short_greeks[k] for k in long_greeks}
    
    @staticmethod
    def _norm_cdf(x):
        """Standard normal CDF"""
        return (1 + np.erf(x/np.sqrt(2))) / 2
    
    def calculate_pnl(self, prices):
        """Calculate P&L across a range of prices"""
        if self.is_call:
            long_payoff = np.maximum(prices - self.long_strike, 0)
            short_payoff = np.maximum(prices - self.short_strike, 0)
        else:
            long_payoff = np.maximum(self.long_strike - prices, 0)
            short_payoff = np.maximum(self.short_strike - prices, 0)
            
        return pd.Series(long_payoff - short_payoff, index=prices)

class MarketData:
    def __init__(self, symbol):
        self.symbol = symbol
        
    def get_current_price(self):
        """Get current price using yfinance"""
        ticker = yf.Ticker(self.symbol)
        return ticker.history(period='1d')['Close'].iloc[-1]
        
    def get_volatility(self):
        """Get 30-day historical volatility"""
        ticker = yf.Ticker(self.symbol)
        hist = ticker.history(period='60d')
        returns = np.log(hist['Close']/hist['Close'].shift(1))
        return returns.std() * np.sqrt(252)

def run_analysis():
    """Run example options analysis"""
    print("Starting Options Analysis Example...")
    
    # Setup strategy
    symbol = "SPY"
    expiry = datetime.now() + timedelta(days=30)
    strikes = (400, 410)  # (long_strike, short_strike)
    strategy = OptionsStrategy(symbol, expiry, strikes, is_call=False)
    
    print(f"\nAnalyzing {strategy.position_type} Spread on {symbol}")
    print(f"Long Strike: {strikes[0]}, Short Strike: {strikes[1]}")
    print(f"Expiry: {expiry.strftime('%Y-%m-%d')}")
    
    # Get market data
    market = MarketData(symbol)
    current_price = market.get_current_price()
    volatility = market.get_volatility()
    risk_free_rate = 0.03  # Assuming 3% risk-free rate
    
    print(f"\nMarket Data:")
    print(f"Current Price: ${current_price:.2f}")
    print(f"Implied Volatility: {volatility:.1%}")
    print(f"Risk-Free Rate: {risk_free_rate:.1%}")
    
    # Calculate Greeks
    greeks = strategy.calculate_greeks(current_price, volatility, risk_free_rate)
    
    print(f"\nStrategy Greeks:")
    for greek, value in greeks.items():
        print(f"{greek.capitalize()}: {value:.4f}")
    
    # Calculate P&L profile
    prices = np.linspace(current_price*0.9, current_price*1.1, 100)
    pnl = strategy.calculate_pnl(prices)
    
    max_profit = pnl.max()
    max_loss = pnl.min()
    breakeven = prices[np.where(pnl >= 0)[0][0]]
    
    print(f"\nStrategy P&L Profile:")
    print(f"Max Profit: ${max_profit:.2f}")
    print(f"Max Loss: ${max_loss:.2f}")
    print(f"Breakeven Price: ${breakeven:.2f}")

if __name__ == "__main__":
    run_analysis()
