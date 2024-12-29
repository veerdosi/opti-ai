# validation.py

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Union
import pandas as pd
import numpy as np

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class StrategyValidator:
    def __init__(self, config):
        self.config = config

    def validate_strategy_parameters(self, strategy) -> None:
        """Validate all strategy parameters"""
        self._validate_expiry(strategy.expiry)
        self._validate_strikes(strategy.long_strike, strategy.short_strike)
        self._validate_symbol(strategy.symbol)

    def _validate_expiry(self, expiry: datetime) -> None:
        """Validate expiration date"""
        days_to_expiry = (expiry - datetime.now()).days

        if days_to_expiry < self.config.strategy.min_days_to_expiry:
            raise ValidationError(
                f"Expiry too soon. Minimum {self.config.strategy.min_days_to_expiry} days required."
            )

        if days_to_expiry > self.config.strategy.max_days_to_expiry:
            raise ValidationError(
                f"Expiry too far. Maximum {self.config.strategy.max_days_to_expiry} days allowed."
            )

    def _validate_strikes(self, long_strike: float, short_strike: float) -> None:
        """Validate strike prices"""
        if long_strike < self.config.strategy.min_strike_price:
            raise ValidationError(f"Long strike below minimum allowed price")

        if short_strike < self.config.strategy.min_strike_price:
            raise ValidationError(f"Short strike below minimum allowed price")

    def _validate_symbol(self, symbol: str) -> None:
        """Validate trading symbol"""
        if not symbol or not isinstance(symbol, str):
            raise ValidationError("Invalid symbol")

class DataValidator:
    def validate_market_data(self, data: pd.DataFrame) -> None:
        """Validate market data"""
        if data.empty:
            raise ValidationError("Empty market data")

        required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            raise ValidationError(f"Missing required columns: {missing_columns}")

        # Check for missing values
        if data[required_columns].isna().any().any():
            raise ValidationError("Market data contains missing values")

        # Validate price relationships
        invalid_prices = (
            (data['High'] < data['Low']) |
            (data['Close'] > data['High']) |
            (data['Close'] < data['Low']) |
            (data['Open'] > data['High']) |
            (data['Open'] < data['Low'])
        )

        if invalid_prices.any():
            bad_dates = data.index[invalid_prices].tolist()
            raise ValidationError(f"Invalid price relationships found on dates: {bad_dates}")

        # Check for extreme price changes
        daily_returns = data['Close'].pct_change()
        extreme_moves = daily_returns.abs() > 0.2  # 20% daily move threshold
        if extreme_moves.any():
            suspicious_dates = data.index[extreme_moves].tolist()
            raise ValidationError(f"Suspicious price movements detected on: {suspicious_dates}")

class PositionValidator:
    def __init__(self, config):
        self.config = config

    def validate_position_size(self, quantity: int, account_value: float,
                             current_positions: List[Dict]) -> None:
        """Validate position size against risk limits"""
        # Check absolute position size
        if abs(quantity) > self.config.strategy.max_position_size:
            raise ValidationError(f"Position size exceeds maximum allowed: {self.config.strategy.max_position_size}")

        # Calculate total exposure
        total_exposure = sum(abs(pos['quantity']) for pos in current_positions)
        new_total = total_exposure + abs(quantity)

        # Check total exposure against account value
        if new_total * self.config.strategy.max_loss_threshold > account_value:
            raise ValidationError("Position would exceed maximum account risk threshold")

class MarketValidator:
    def __init__(self, config):
        self.config = config

    def validate_market_hours(self) -> None:
        """Validate if we're in market hours"""
        now = datetime.now().time()
        market_start = datetime.strptime(self.config.market.market_hours_start, "%H:%M").time()
        market_end = datetime.strptime(self.config.market.market_hours_end, "%H:%M").time()

        if not (market_start <= now <= market_end):
            raise ValidationError("Outside of market hours")

    def validate_market_conditions(self, data: pd.DataFrame) -> None:
        """Validate market conditions"""
        if len(data) < 20:  # Need at least 20 days for volatility calculation
            raise ValidationError("Insufficient historical data for analysis")

        # Calculate volatility
        returns = data['Close'].pct_change()
        volatility = returns.std() * np.sqrt(252)

        # Check for extreme volatility
        if volatility > 0.5:  # 50% annualized volatility threshold
            raise ValidationError("Market volatility too high for safe trading")

def validate_strategy(strategy, config, market_data: pd.DataFrame,
                     account_value: float, current_positions: List[Dict]) -> None:
    """Main validation function"""
    strategy_validator = StrategyValidator(config)
    data_validator = DataValidator()
    position_validator = PositionValidator(config)
    market_validator = MarketValidator(config)

    # Run all validations
    strategy_validator.validate_strategy_parameters(strategy)
    data_validator.validate_market_data(market_data)
    position_validator.validate_position_size(1, account_value, current_positions)
    market_validator.validate_market_hours()
    market_validator.validate_market_conditions(market_data)
