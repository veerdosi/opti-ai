from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import threading
import queue
import time

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    price: float
    bid: float
    ask: float
    volume: int
    implied_volatility: float

@dataclass
class Position:
    contract_id: int
    symbol: str
    quantity: int
    average_cost: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float

class IBKRConnection:
    """
    Simulated IBKR connection class
    In production, replace with actual IB API calls
    """
    def __init__(self):
        self.connected = False
        self.market_data_queue = queue.Queue()
        self.positions: Dict[int, Position] = {}
        self.orders: Dict[int, Dict] = {}
        self._next_order_id = 1
        self._stop_streaming = False
        
    def connect(self, host: str = "127.0.0.1", port: int = 7497, 
                client_id: int = 1) -> bool:
        """
        Establish connection to IBKR TWS or Gateway
        In production, implement actual connection logic
        """
        self.connected = True
        return True
        
    def disconnect(self):
        """Disconnect from IBKR"""
        self._stop_streaming = True
        self.connected = False
        
    def request_market_data(self, symbol: str) -> None:
        """
        Request real-time market data for a symbol
        Starts a background thread to simulate market data
        """
        def _stream_market_data():
            while not self._stop_streaming:
                # Simulate market data
                current_price = 100 + np.random.normal(0, 1)
                data = MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=current_price,
                    bid=current_price - 0.01,
                    ask=current_price + 0.01,
                    volume=int(np.random.exponential(1000)),
                    implied_volatility=0.2 + np.random.normal(0, 0.01)
                )
                self.market_data_queue.put(data)
                time.sleep(1)
                
        thread = threading.Thread(target=_stream_market_data)
        thread.daemon = True
        thread.start()

class PositionMonitor:
    def __init__(self, ibkr_connection: IBKRConnection):
        self.ibkr = ibkr_connection
        self.positions: Dict[str, Position] = {}
        self._stop_monitoring = False
        
    def start_monitoring(self):
        """Start position monitoring in a separate thread"""
        def _monitor_positions():
            while not self._stop_monitoring:
                # Update positions
                for contract_id, position in self.ibkr.positions.items():
                    self.positions[position.symbol] = position
                time.sleep(1)
                
        thread = threading.Thread(target=_monitor_positions)
        thread.daemon = True
        thread.start()
        
    def stop_monitoring(self):
        """Stop position monitoring"""
        self._stop_monitoring = True
        
    def get_position_summary(self) -> Dict[str, Dict]:
        """Get summary of all positions"""
        summary = {}
        for symbol, position in self.positions.items():
            summary[symbol] = {
                "quantity": position.quantity,
                "avg_cost": position.average_cost,
                "market_value": position.market_value,
                "unrealized_pnl": position.unrealized_pnl,
                "realized_pnl": position.realized_pnl
            }
        return summary

class PaperTrading:
    def __init__(self, ibkr_connection: IBKRConnection):
        self.ibkr = ibkr_connection
        self.orders: Dict[int, Dict] = {}
        self.positions: Dict[str, Position] = {}
        self.cash_balance = 1000000  # Initial paper trading balance
        
    def place_order(self, symbol: str, quantity: int, 
                   order_type: str = "MKT") -> int:
        """Place a paper trading order"""
        order_id = self.ibkr._next_order_id
        self.ibkr._next_order_id += 1
        
        # Simulate order execution
        market_data = self.ibkr.market_data_queue.get()
        execution_price = market_data.price
        
        order = {
            "order_id": order_id,
            "symbol": symbol,
            "quantity": quantity,
            "order_type": order_type,
            "status": "FILLED",
            "filled_price": execution_price,
            "timestamp": datetime.now()
        }
        
        self.orders[order_id] = order
        
        # Update position
        if symbol not in self.positions:
            self.positions[symbol] = Position(
                contract_id=order_id,
                symbol=symbol,
                quantity=quantity,
                average_cost=execution_price,
                market_value=quantity * execution_price,
                unrealized_pnl=0,
                realized_pnl=0
            )
        else:
            position = self.positions[symbol]
            new_quantity = position.quantity + quantity
            if new_quantity == 0:
                # Position closed
                realized_pnl = (execution_price - position.average_cost) * abs(position.quantity)
                position.realized_pnl += realized_pnl
                del self.positions[symbol]
            else:
                # Update position
                position.quantity = new_quantity
                position.average_cost = (position.average_cost * position.quantity + 
                                      execution_price * quantity) / new_quantity
                position.market_value = new_quantity * execution_price
        
        # Update cash balance
        self.cash_balance -= quantity * execution_price
        
        return order_id
    
    def get_order_status(self, order_id: int) -> Optional[Dict]:
        """Get status of a specific order"""
        return self.orders.get(order_id)
    
    def get_portfolio_summary(self) -> Dict:
        """Get summary of paper trading portfolio"""
        total_market_value = sum(pos.market_value for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.positions.values())
        
        return {
            "cash_balance": self.cash_balance,
            "market_value": total_market_value,
            "total_value": self.cash_balance + total_market_value,
            "unrealized_pnl": total_unrealized_pnl,
            "realized_pnl": total_realized_pnl
        }

class MarketDataManager:
    def __init__(self, ibkr_connection: IBKRConnection):
        self.ibkr = ibkr_connection
        self.data_cache: Dict[str, List[MarketData]] = {}
        self._stop_collecting = False
        
    def start_collecting(self, symbols: List[str]):
        """Start collecting market data for specified symbols"""
        for symbol in symbols:
            self.ibkr.request_market_data(symbol)
            self.data_cache[symbol] = []
            
        def _collect_data():
            while not self._stop_collecting:
                try:
                    data = self.ibkr.market_data_queue.get(timeout=1)
                    self.data_cache[data.symbol].append(data)
                    # Keep only last 1000 data points per symbol
                    if len(self.data_cache[data.symbol]) > 1000:
                        self.data_cache[data.symbol].pop(0)
                except queue.Empty:
                    continue
                
        thread = threading.Thread(target=_collect_data)
        thread.daemon = True
        thread.start()
    
    def stop_collecting(self):
        """Stop collecting market data"""
        self._stop_collecting = True
        
    def get_latest_data(self, symbol: str) -> Optional[MarketData]:
        """Get the latest market data for a symbol"""
        if symbol in self.data_cache and self.data_cache[symbol]:
            return self.data_cache[symbol][-1]
        return None
    
    def get_historical_data(self, symbol: str, 
                          lookback: int = 100) -> List[MarketData]:
        """Get historical market data for a symbol"""
        if symbol in self.data_cache:
            return self.data_cache[symbol][-lookback:]
        return []

class TradingSystem:
    """Main trading system that integrates all components"""
    
    def __init__(self):
        self.ibkr = IBKRConnection()
        self.market_data = MarketDataManager(self.ibkr)
        self.position_monitor = PositionMonitor(self.ibkr)
        self.paper_trading = PaperTrading(self.ibkr)
        self.active_strategies: Dict[str, Dict] = {}
        
    def initialize(self):
        """Initialize the trading system"""
        # Connect to IBKR
        if not self.ibkr.connect():
            raise ConnectionError("Failed to connect to IBKR")
        
        # Start position monitoring
        self.position_monitor.start_monitoring()
        
    def shutdown(self):
        """Shutdown the trading system"""
        self.market_data.stop_collecting()
        self.position_monitor.stop_monitoring()
        self.ibkr.disconnect()
        
    def add_strategy(self, strategy_name: str, 
                    strategy_config: Dict,
                    symbols: List[str]):
        """Add a new trading strategy to monitor"""
        self.active_strategies[strategy_name] = {
            'config': strategy_config,
            'symbols': symbols,
            'active_orders': set(),
            'positions': {}
        }
        
        # Start collecting market data for strategy symbols
        self.market_data.start_collecting(symbols)
        
    def execute_paper_trade(self, strategy_name: str, 
                          symbol: str, 
                          quantity: int) -> Optional[int]:
        """Execute a paper trade for a strategy"""
        if strategy_name not in self.active_strategies:
            return None
            
        order_id = self.paper_trading.place_order(symbol, quantity)
        self.active_strategies[strategy_name]['active_orders'].add(order_id)
        return order_id
        
    def get_strategy_status(self, strategy_name: str) -> Dict:
        """Get current status of a strategy"""
        if strategy_name not in self.active_strategies:
            return {}
            
        strategy = self.active_strategies[strategy_name]
        positions = {}
        for symbol in strategy['symbols']:
            latest_data = self.market_data.get_latest_data(symbol)
            if latest_data:
                positions[symbol] = {
                    'price': latest_data.price,
                    'implied_vol': latest_data.implied_volatility,
                    'position': self.position_monitor.positions.get(symbol)
                }
                
        return {
            'positions': positions,
            'portfolio': self.paper_trading.get_portfolio_summary(),
            'active_orders': len(strategy['active_orders'])
        }
        
    def generate_trading_signals(self, strategy_name: str) -> List[Dict]:
        """Generate trading signals based on strategy configuration"""
        if strategy_name not in self.active_strategies:
            return []
            
        strategy = self.active_strategies[strategy_name]
        signals = []
        
        for symbol in strategy['symbols']:
            historical_data = self.market_data.get_historical_data(symbol)
            if not historical_data:
                continue
                
            # Convert market data to DataFrame for analysis
            df = pd.DataFrame([{
                'timestamp': d.timestamp,
                'price': d.price,
                'volume': d.volume,
                'implied_vol': d.implied_volatility
            } for d in historical_data])
            
            # Apply strategy-specific signal generation logic
            config = strategy['config']
            signal = self._apply_strategy_rules(df, config)
            if signal:
                signals.append({
                    'symbol': symbol,
                    'action': signal['action'],
                    'quantity': signal['quantity'],
                    'timestamp': datetime.now(),
                    'reason': signal['reason']
                })
                
        return signals
        
    def _apply_strategy_rules(self, 
                            data: pd.DataFrame, 
                            config: Dict) -> Optional[Dict]:
        """Apply strategy-specific trading rules"""
        # Implement strategy logic based on configuration
        # This is a simplified example
        if len(data) < 2:
            return None
            
        latest_price = data.iloc[-1]['price']
        prev_price = data.iloc[-2]['price']
        
        if 'threshold' in config:
            threshold = config['threshold']
            if latest_price > prev_price * (1 + threshold):
                return {
                    'action': 'SELL',
                    'quantity': 1,
                    'reason': f'Price increased above threshold: {threshold}'
                }
            elif latest_price < prev_price * (1 - threshold):
                return {
                    'action': 'BUY',
                    'quantity': 1,
                    'reason': f'Price decreased below threshold: {threshold}'
                }
                
        return None

def create_trading_system() -> TradingSystem:
    """Factory function to create and initialize a trading system"""
    system = TradingSystem()
    try:
        system.initialize()
        return system
    except Exception as e:
        print(f"Failed to initialize trading system: {e}")
        raise