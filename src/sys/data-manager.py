import yfinance as yf
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np
from pathlib import Path
import logging
import json

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

            # Create strategy data table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_data (
                    strategy TEXT,
                    date DATE,
                    symbol TEXT,
                    position_type TEXT,
                    quantity INTEGER,
                    entry_price REAL,
                    current_price REAL,
                    pnl REAL,
                    delta REAL,
                    gamma REAL,
                    theta REAL,
                    vega REAL,
                    PRIMARY KEY (strategy, symbol, date)
                )
            """)
            
            # Create strategy metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_metrics (
                    strategy TEXT PRIMARY KEY,
                    metrics TEXT,
                    last_updated TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def fetch_historical_data(self, config: MarketDataConfig) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical market data for specified symbols
        """
        data_dict = {}
        
        for symbol in config.symbols:
            try:
                # Check cache first
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

    # Strategy Data Management Methods
    def save_strategy_data(self, strategy_name: str, data: pd.DataFrame):
        """Save strategy data to database"""
        with sqlite3.connect(self.db_path) as conn:
            # Add strategy name column if not exists
            if 'strategy' not in data.columns:
                data['strategy'] = strategy_name
            
            # Convert datetime to string for SQLite
            if 'date' in data.columns and isinstance(data['date'].iloc[0], datetime):
                data['date'] = data['date'].dt.strftime('%Y-%m-%d')
            
            data.to_sql('strategy_data', conn, if_exists='append', index=False)

    def get_strategy_data(self, strategy_name: Optional[str] = None) -> pd.DataFrame:
        """Retrieve strategy data from database"""
        query = "SELECT * FROM strategy_data"
        if strategy_name:
            query += f" WHERE strategy = '{strategy_name}'"
            
        with sqlite3.connect(self.db_path) as conn:
            data = pd.read_sql_query(query, conn)
            
            # Convert date strings back to datetime
            if 'date' in data.columns:
                data['date'] = pd.to_datetime(data['date'])
                
        return data

    def update_strategy_metrics(self, strategy_name: str, metrics: Dict):
        """Update strategy metrics in database"""
        with sqlite3.connect(self.db_path) as conn:
            metrics_json = json.dumps(metrics)
            
            conn.execute("""
                INSERT OR REPLACE INTO strategy_metrics (strategy, metrics, last_updated)
                VALUES (?, ?, datetime('now'))
            """, (strategy_name, metrics_json))
            
            conn.commit()

    def get_strategy_metrics(self, strategy_name: str) -> Optional[Dict]:
        """Get strategy metrics from database"""
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute(
                "SELECT metrics FROM strategy_metrics WHERE strategy = ?",
                (strategy_name,)
            ).fetchone()
            
            if result:
                return json.loads(result[0])
        return None

    def _validate_market_data(self, data: pd.DataFrame, symbol: str):
        """Validate market data for common issues"""
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
            pct_change = data[col].pct_change().abs()
            anomalies = pct_change > 0.5  # 50% price change threshold
            if anomalies.any():
                self.logger.warning(
                    f"Large price changes detected in {symbol} {col}"
                )
                
    def _clean_market_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean and process market data"""
        cleaned = data.copy()
        cleaned = cleaned.ffill()  # Forward fill missing values
        
        # Calculate additional metrics
        cleaned['returns'] = cleaned['Close'].pct_change()
        cleaned['volatility'] = cleaned['returns'].rolling(window=20).std() * np.sqrt(252)
        cleaned['SMA_20'] = cleaned['Close'].rolling(window=20).mean()
        cleaned['SMA_50'] = cleaned['Close'].rolling(window=50).mean()
        
        cleaned = cleaned.dropna()  # Drop any remaining NaN values
        return cleaned
    
    def _store_market_data(self, symbol: str, data: pd.DataFrame):
        """Store market data in SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            to_store = data.reset_index()
            to_store['symbol'] = symbol
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
