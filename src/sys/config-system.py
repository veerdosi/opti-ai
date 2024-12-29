# config.py

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import json
from datetime import datetime, timedelta

@dataclass
class DatabaseConfig:
    path: str = "market_data.db"
    backup_path: Optional[str] = None
    max_connections: int = 5

@dataclass
class MarketConfig:
    risk_free_rate: float = 0.03  # 3% risk-free rate
    market_hours_start: str = "09:30"
    market_hours_end: str = "16:00"
    default_volatility: float = 0.2  # 20% default volatility

@dataclass
class StrategyConfig:
    min_days_to_expiry: int = 7
    max_days_to_expiry: int = 45
    min_strike_price: float = 1.0
    max_position_size: int = 10
    max_loss_threshold: float = 0.5  # 50% of account value
    default_account_value: float = 100000  # $100k default account value

@dataclass
class Config:
    database: DatabaseConfig
    market: MarketConfig
    strategy: StrategyConfig
    
    @classmethod
    def load_config(cls, config_path: str = "config.json") -> 'Config':
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r') as f:
                config_dict = json.load(f)
                
            return cls(
                database=DatabaseConfig(**config_dict.get('database', {})),
                market=MarketConfig(**config_dict.get('market', {})),
                strategy=StrategyConfig(**config_dict.get('strategy', {}))
            )
        except FileNotFoundError:
            # Return default configuration if file doesn't exist
            return cls(
                database=DatabaseConfig(),
                market=MarketConfig(),
                strategy=StrategyConfig()
            )
    
    def save_config(self, config_path: str = "config.json"):
        """Save configuration to JSON file"""
        config_dict = {
            'database': {
                'path': self.database.path,
                'backup_path': self.database.backup_path,
                'max_connections': self.database.max_connections
            },
            'market': {
                'risk_free_rate': self.market.risk_free_rate,
                'market_hours_start': self.market.market_hours_start,
                'market_hours_end': self.market.market_hours_end,
                'default_volatility': self.market.default_volatility
            },
            'strategy': {
                'min_days_to_expiry': self.strategy.min_days_to_expiry,
                'max_days_to_expiry': self.strategy.max_days_to_expiry,
                'min_strike_price': self.strategy.min_strike_price,
                'max_position_size': self.strategy.max_position_size,
                'max_loss_threshold': self.strategy.max_loss_threshold,
                'default_account_value': self.strategy.default_account_value
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_dict, f, indent=4)
