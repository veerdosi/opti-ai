from ib_insync import *
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import logging
from queue import Queue
import threading
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

class IBKRClient:
    """
    Unified IBKR client handling both live and paper trading
    """
    def __init__(self, is_paper_trading: bool = True):
        self.ib = IB()
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.contracts = {}
        self.market_data = {}
        self.is_paper_trading = is_paper_trading
        
        # Paper trading specific attributes
        if is_paper_trading:
            self.paper_positions: Dict[int, Position] = {}
            self.paper_orders: Dict[int, Dict] = {}
            self._next_order_id = 1
            self.cash_balance = 1000000  # Initial paper trading balance
            self.market_data_queue = Queue()
            self._stop_streaming = False

    def connect(self, host: str = "127.0.0.1", port: int = 7497, 
                client_id: int = 1) -> bool:
        """Connect to IBKR TWS or Gateway"""
        try:
            self.ib.connect(host, port, clientId=client_id)
            self.connected = True
            self.logger.info(f"Connected to IBKR at {host}:{port}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to IBKR: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from IBKR"""
        if self.connected:
            if self.is_paper_trading:
                self._stop_streaming = True
            self.ib.disconnect()
            self.connected = False

    def _create_contract(self, symbol: str) -> Optional[Contract]:
        """Create an IBKR contract object"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            self.ib.qualifyContracts(contract)
            return contract
        except Exception as e:
            self.logger.error(f"Failed to create contract for {symbol}: {e}")
            return None

    def request_market_data(self, symbol: str) -> None:
        """Request real-time market data for a symbol"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return

        try:
            # Create contract if not exists
            if symbol not in self.contracts:
                contract = self._create_contract(symbol)
                if not contract:
                    return
                self.contracts[symbol] = contract

            if self.is_paper_trading:
                self._start_paper_market_data(symbol)
            else:
                self._start_live_market_data(symbol)

        except Exception as e:
            self.logger.error(f"Failed to request market data for {symbol}: {e}")

    def _start_live_market_data(self, symbol: str):
        """Handle live market data streaming"""
        ticker = self.ib.reqMktData(self.contracts[symbol])
        
        def on_tick_event(ticker):
            if ticker.contract.symbol == symbol:
                self.market_data[symbol] = MarketData(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    price=ticker.last if ticker.last else ticker.close,
                    bid=ticker.bid if ticker.bid else 0,
                    ask=ticker.ask if ticker.ask else 0,
                    volume=ticker.volume if ticker.volume else 0,
                    implied_volatility=ticker.optVolume if ticker.optVolume else 0
                )
                
        ticker.updateEvent += on_tick_event

    def _start_paper_market_data(self, symbol: str):
        """Simulate market data for paper trading"""
        def _stream_market_data():
            while not self._stop_streaming:
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

    def place_order(self, symbol: str, quantity: int, 
                   order_type: str = "MKT", limit_price: float = None) -> Optional[int]:
        """Place an order (live or paper)"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return None

        try:
            if self.is_paper_trading:
                return self._place_paper_order(symbol, quantity, order_type, limit_price)
            else:
                return self._place_live_order(symbol, quantity, order_type, limit_price)

        except Exception as e:
            self.logger.error(f"Failed to place order for {symbol}: {e}")
            return None

    def _place_live_order(self, symbol: str, quantity: int, 
                         order_type: str, limit_price: float) -> Optional[int]:
        """Place a live order through IBKR"""
        if symbol not in self.contracts:
            contract = self._create_contract(symbol)
            if not contract:
                return None
            self.contracts[symbol] = contract

        # Create order object
        if order_type == "MKT":
            order = MarketOrder("BUY" if quantity > 0 else "SELL", abs(quantity))
        elif order_type == "LMT" and limit_price:
            order = LimitOrder("BUY" if quantity > 0 else "SELL", 
                             abs(quantity), limit_price)
        else:
            self.logger.error("Invalid order type or missing limit price")
            return None

        # Place order
        trade = self.ib.placeOrder(self.contracts[symbol], order)
        return trade.order.orderId

    def _place_paper_order(self, symbol: str, quantity: int,
                          order_type: str, limit_price: float) -> int:
        """Place a paper trading order"""
        order_id = self._next_order_id
        self._next_order_id += 1

        # Simulate order execution
        market_data = self.market_data_queue.get()
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

        self.paper_orders[order_id] = order
        self._update_paper_position(symbol, quantity, execution_price)
        return order_id

    def _update_paper_position(self, symbol: str, quantity: int, price: float):
        """Update paper trading position"""
        if symbol not in self.paper_positions:
            self.paper_positions[symbol] = Position(
                contract_id=len(self.paper_positions) + 1,
                symbol=symbol,
                quantity=quantity,
                average_cost=price,
                market_value=quantity * price,
                unrealized_pnl=0,
                realized_pnl=0
            )
        else:
            pos = self.paper_positions[symbol]
            new_quantity = pos.quantity + quantity
            if new_quantity == 0:
                # Position closed
                realized_pnl = (price - pos.average_cost) * abs(pos.quantity)
                pos.realized_pnl += realized_pnl
                del self.paper_positions[symbol]
            else:
                # Update position
                pos.quantity = new_quantity
                pos.average_cost = (pos.average_cost * pos.quantity + 
                                  price * quantity) / new_quantity
                pos.market_value = new_quantity * price

        # Update cash balance
        self.cash_balance -= quantity * price

    def get_positions(self) -> List[Dict]:
        """Get current positions (live or paper)"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return []

        try:
            if self.is_paper_trading:
                return [{
                    'symbol': pos.symbol,
                    'quantity': pos.quantity,
                    'avg_cost': pos.average_cost,
                    'market_value': pos.market_value,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl
                } for pos in self.paper_positions.values()]
            else:
                positions = self.ib.positions()
                return [{
                    'symbol': pos.contract.symbol,
                    'quantity': pos.position,
                    'avg_cost': pos.avgCost,
                    'market_value': pos.marketValue if hasattr(pos, 'marketValue') else 0
                } for pos in positions]

        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []

    def get_portfolio_summary(self) -> Dict:
        """Get portfolio summary (paper trading only)"""
        if not self.is_paper_trading:
            self.logger.error("Portfolio summary only available for paper trading")
            return {}

        total_market_value = sum(pos.market_value for pos in self.paper_positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.paper_positions.values())
        total_realized_pnl = sum(pos.realized_pnl for pos in self.paper_positions.values())

        return {
            "cash_balance": self.cash_balance,
            "market_value": total_market_value,
            "total_value": self.cash_balance + total_market_value,
            "unrealized_pnl": total_unrealized_pnl,
            "realized_pnl": total_realized_pnl
        }
