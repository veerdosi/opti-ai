import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import logging

@dataclass
class MarketDataConfig:
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    interval: str = "1d"
    adjust_prices: bool = True
    validate_data: bool = True
    
class DataValidationError(Exception):
    """Custom exception for data validation errors"""
    pass

class MarketDataManager:
    def __init__(self, db_path: str = "market_data.db"):
        """
        Initialize the Market Data Manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._initialize_database()
        
    def _initialize_database(self):
        """Create necessary database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create market data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    symbol TEXT,
                    date DATE,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    adjusted_close REAL,
                    implied_volatility REAL,
                    PRIMARY KEY (symbol, date)
                )
            """)
            
            # Create options data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS options_data (
                    symbol TEXT,
                    date DATE,
                    strike REAL,
                    expiry DATE,
                    option_type TEXT,
                    bid REAL,
                    ask REAL,
                    volume INTEGER,
                    open_interest INTEGER,
                    implied_volatility REAL,
                    delta REAL,
                    gamma REAL,
                    theta REAL,
                    vega REAL,
                    PRIMARY KEY (symbol, date, strike, expiry, option_type)
                )
            """)
            
            conn.commit()
    
    def fetch_historical_data(self, config: MarketDataConfig) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical market data for specified symbols
        
        Args:
            config: MarketDataConfig object with fetch parameters
            
        Returns:
            Dictionary mapping symbols to their respective DataFrames
        """
        data_dict = {}
        
        for symbol in config.symbols:
            try:
                # Check if we have data in database
                cached_data = self._get_cached_data(
                    symbol, 
                    config.start_date, 
                    config.end_date
                )
                
                if cached_data is not None:
                    self.logger.info(f"Using cached data for {symbol}")
                    data_dict[symbol] = cached_data
                    continue
                
                # Fetch new data from yfinance
                ticker = yf.Ticker(symbol)
                data = ticker.history(
                    start=config.start_date,
                    end=config.end_date,
                    interval=config.interval
                )
                
                if config.validate_data:
                    self._validate_market_data(data, symbol)
                
                # Clean and process the data
                data = self._clean_market_data(data)
                
                # Store in database
                self._store_market_data(symbol, data)
                
                data_dict[symbol] = data
                
            except Exception as e:
                self.logger.error(f"Error fetching data for {symbol}: {str(e)}")
                raise
                
        return data_dict
    
    def _validate_market_data(self, data: pd.DataFrame, symbol: str):
        """
        Validate market data for common issues
        
        Args:
            data: DataFrame containing market data
            symbol: Symbol being validated
        
        Raises:
            DataValidationError: If validation fails
        """
        if data.empty:
            raise DataValidationError(f"No data received for {symbol}")
            
        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise DataValidationError(
                f"Missing required columns for {symbol}: {missing_columns}"
            )
            
        # Check for missing values
        if data[required_columns].isna().any().any():
            self.logger.warning(f"Missing values detected in {symbol} data")
            
        # Check for price anomalies
        price_cols = ['Open', 'High', 'Low', 'Close']
        for col in price_cols:
            # Detect extreme price changes
            pct_change = data[col].pct_change().abs()
            anomalies = pct_change > 0.5  # 50% price change threshold
            if anomalies.any():
                self.logger.warning(
                    f"Large price changes detected in {symbol} {col}"
                )
                
    def _clean_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process market data
        
        Args:
            data: Raw market data DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Create copy to avoid modifying original
        cleaned = data.copy()
        
        # Forward fill missing values
        cleaned = cleaned.ffill()
        
        # Calculate additional metrics
        cleaned['returns'] = cleaned['Close'].pct_change()
        cleaned['volatility'] = cleaned['returns'].rolling(window=20).std() * np.sqrt(252)
        
        # Add technical indicators
        cleaned['SMA_20'] = cleaned['Close'].rolling(window=20).mean()
        cleaned['SMA_50'] = cleaned['Close'].rolling(window=50).mean()
        
        # Drop any remaining NaN values
        cleaned = cleaned.dropna()
        
        return cleaned
    
    def _store_market_data(self, symbol: str, data: pd.DataFrame):
        """Store market data in SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            # Prepare data for storage
            to_store = data.reset_index()
            to_store['symbol'] = symbol
            
            # Store in database
            to_store.to_sql('market_data', conn, if_exists='append', index=False)
            
    def _get_cached_data(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """Retrieve cached data from database if available"""
        query = """
            SELECT * FROM market_data 
            WHERE symbol = ? AND date BETWEEN ? AND ?
            ORDER BY date
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(
                query, 
                conn, 
                params=(symbol, start_date, end_date),
                parse_dates=['date']
            )
            
            if len(df) > 0:
                df = df.set_index('date')
                return df
                
        return None
    
    def get_options_chain(
        self, 
        symbol: str, 
        expiry_range: Optional[Tuple[datetime, datetime]] = None
    ) -> pd.DataFrame:
        """
        Fetch current options chain for a symbol
        
        Args:
            symbol: Stock symbol
            expiry_range: Optional tuple of (start_date, end_date) for expiries
            
        Returns:
            DataFrame containing options chain data
        """
        ticker = yf.Ticker(symbol)
        
        # Get list of expiries
        expiries = ticker.options
        
        if expiry_range:
            start_date, end_date = expiry_range
            expiries = [
                exp for exp in expiries 
                if start_date <= datetime.strptime(exp, '%Y-%m-%d') <= end_date
            ]
        
        chains = []
        for expiry in expiries:
            try:
                # Fetch both calls and puts
                opt = ticker.option_chain(expiry)
                
                # Combine calls and puts
                calls = opt.calls
                calls['option_type'] = 'call'
                puts = opt.puts
                puts['option_type'] = 'put'
                
                chain = pd.concat([calls, puts])
                chain['expiry'] = expiry
                chains.append(chain)
                
            except Exception as e:
                self.logger.error(f"Error fetching options for {expiry}: {str(e)}")
                continue
                
        if not chains:
            raise DataValidationError(f"No valid options data found for {symbol}")
            
        # Combine all chains
        options_data = pd.concat(chains, ignore_index=True)
        
        # Store in database
        self._store_options_data(symbol, options_data)
        
        return options_data
    
    def _store_options_data(self, symbol: str, data: pd.DataFrame):
        """Store options data in SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            data['symbol'] = symbol
            data['date'] = datetime.now().date()
            
            # Store in database
            data.to_sql('options_data', conn, if_exists='append', index=False)
            
    def get_historical_volatility(
        self, 
        symbol: str, 
        window: int = 30
    ) -> pd.Series:
        """
        Calculate historical volatility for a symbol
        
        Args:
            symbol: Stock symbol
            window: Rolling window for volatility calculation
            
        Returns:
            Series of historical volatility values
        """
        # Get historical data
        data = self.fetch_historical_data(MarketDataConfig(
            symbols=[symbol],
            start_date=datetime.now() - timedelta(days=window*2),
            end_date=datetime.now()
        ))[symbol]
        
        # Calculate daily returns
        returns = data['Close'].pct_change()
        
        # Calculate rolling volatility
        volatility = returns.rolling(
            window=window
        ).std() * np.sqrt(252)  # Annualize
        
        return volatility
