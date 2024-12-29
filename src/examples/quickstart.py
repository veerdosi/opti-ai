# quickstart.py

from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import sqlite3
from dataclasses import dataclass
from config import Config, DatabaseConfig, MarketConfig, StrategyConfig

@dataclass
class OptionsStrategy:
    symbol: str
    expiry: datetime
    long_strike: float
    short_strike: float
    is_call: bool
    position_type: str = None
    
    def __post_init__(self):
        self.position_type = "Bear Call" if self.is_call else "Bull Put"
        
    def calculate_greeks(self, current_price, volatility, risk_free_rate):
        """Calculate option Greeks using Black-Scholes"""
        # Time to expiry in years
        tte = (self.expiry - datetime.now()).days / 365
        if tte <= 0:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
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

class StrategyAnalyzer:
    def __init__(self, config: Config):
        self.config = config
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.config.database.path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_data (
                    date TEXT,
                    strategy TEXT,
                    symbol TEXT,
                    price REAL,
                    delta REAL,
                    gamma REAL,
                    theta REAL,
                    vega REAL,
                    pnl REAL
                )
            """)
    
    def save_results(self, results_df: pd.DataFrame):
        """Save analysis results to database"""
        with sqlite3.connect(self.config.database.path) as conn:
            results_df.to_sql('strategy_data', conn, if_exists='append', index=False)

def run_analysis():
    """Run complete options analysis example"""
    print("\nStarting Options Analysis Example...")
    
    # Load configuration
    config = Config.load_config()
    print("\nConfiguration loaded successfully")
    
    try:
        # Setup strategy parameters
        symbol = "SPY"
        expiry = datetime.now() + timedelta(days=30)
        
        # Fetch market data
        print("\nFetching market data...")
        ticker = yf.Ticker(symbol)
        current_price = ticker.history(period='1d')['Close'].iloc[-1]
        historical_data = ticker.history(period="60d")
        
        # Calculate suitable strike prices based on current price
        long_strike = round(current_price * 0.95 / 5) * 5  # 5% OTM for long strike
        short_strike = round(current_price * 0.97 / 5) * 5  # 3% OTM for short strike
        
        strategy = OptionsStrategy(
            symbol=symbol,
            expiry=expiry,
            long_strike=long_strike,
            short_strike=short_strike,
            is_call=False  # Bull Put Spread
        )
        
        print(f"\nStrategy Setup:")
        print(f"Type: {strategy.position_type} Spread")
        print(f"Symbol: {symbol}")
        print(f"Current Price: ${current_price:.2f}")
        print(f"Long Strike: ${strategy.long_strike}")
        print(f"Short Strike: ${strategy.short_strike}")
        print(f"Expiry: {expiry.strftime('%Y-%m-%d')}")
        
        # Initialize analyzer
        analyzer = StrategyAnalyzer(config)
        
        # Calculate strategy metrics
        print("\nCalculating strategy metrics...")
        results = []
        
        for date, row in historical_data.iterrows():
            price = row['Close']
            volatility = historical_data['Close'].pct_change().std() * np.sqrt(252)
            
            # Calculate Greeks
            greeks = strategy.calculate_greeks(
                price, 
                volatility,
                config.market.risk_free_rate
            )
            
            # Calculate PnL
            pnl = strategy.calculate_pnl(pd.Series([price]))[0]
            
            results.append({
                'date': date.strftime('%Y-%m-%d'),
                'strategy': strategy.position_type,
                'symbol': symbol,
                'price': price,
                'pnl': pnl,
                **greeks
            })
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        # Save results
        analyzer.save_results(results_df)
        
        # Display performance summary
        print("\nStrategy Performance Summary:")
        print(f"Total P&L: ${results_df['pnl'].sum():.2f}")
        print(f"Max Profit: ${results_df['pnl'].max():.2f}")
        print(f"Max Loss: ${results_df['pnl'].min():.2f}")
        print(f"Win Rate: {(results_df['pnl'] > 0).mean():.1%}")
        
        # Plot results
        plot_strategy_results(results_df, strategy.position_type)
        
        print(f"\nAnalysis complete! Results saved to: {config.database.path}")
        
    except Exception as e:
        print(f"\nError during analysis: {str(e)}")
        raise

def plot_strategy_results(results_df: pd.DataFrame, strategy_type: str):
    """Create visualization plots for strategy results"""
    # P&L Plot
    plt.figure(figsize=(12, 6))
    plt.plot(pd.to_datetime(results_df['date']), results_df['pnl'])
    plt.title(f"{strategy_type} Spread P&L")
    plt.xlabel("Date")
    plt.ylabel("P&L ($)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    # Greeks Plot
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Options Greeks Over Time")
    
    dates = pd.to_datetime(results_df['date'])
    
    axes[0, 0].plot(dates, results_df['delta'])
    axes[0, 0].set_title("Delta")
    axes[0, 0].grid(True)
    
    axes[0, 1].plot(dates, results_df['gamma'])
    axes[0, 1].set_title("Gamma")
    axes[0, 1].grid(True)
    
    axes[1, 0].plot(dates, results_df['theta'])
    axes[1, 0].set_title("Theta")
    axes[1, 0].grid(True)
    
    axes[1, 1].plot(dates, results_df['vega'])
    axes[1, 1].set_title("Vega")
    axes[1, 1].grid(True)
    
    for ax in axes.flat:
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    run_analysis()
