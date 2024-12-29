from ib_insync import *
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import logging

@dataclass
class MarketData:
    symbol: str
    timestamp: datetime
    price: float
    bid: float
    ask: float
    volume: int
    implied_volatility: float

class IBKRLiveClient:
    def __init__(self):
        self.ib = IB()
        self.connected = False
        self.logger = logging.getLogger(__name__)
        self.contracts = {}
        self.market_data = {}
        
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
            self.ib.disconnect()
            self.connected = False
            
    def _create_contract(self, symbol: str) -> Optional[Contract]:
        """Create an IBKR contract object"""
        try:
            contract = Stock(symbol, 'SMART', 'USD')
            # Ensure contract details are available
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
                
            # Request market data
            ticker = self.ib.reqMktData(self.contracts[symbol])
            
            # Set up callback for market data updates
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
            
        except Exception as e:
            self.logger.error(f"Failed to request market data for {symbol}: {e}")
            
    def get_historical_data(self, symbol: str, duration: str = "1 Y",
                           bar_size: str = "1 day") -> pd.DataFrame:
        """Get historical market data"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return pd.DataFrame()
            
        try:
            if symbol not in self.contracts:
                contract = self._create_contract(symbol)
                if not contract:
                    return pd.DataFrame()
                self.contracts[symbol] = contract
                
            bars = self.ib.reqHistoricalData(
                self.contracts[symbol],
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='TRADES',
                useRTH=True
            )
            
            # Convert to DataFrame
            df = util.df(bars)
            return df
            
        except Exception as e:
            self.logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()
            
    def place_order(self, symbol: str, quantity: int, 
                   order_type: str = "MKT", limit_price: float = None) -> Optional[int]:
        """Place a real order through IBKR"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return None
            
        try:
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
            
        except Exception as e:
            self.logger.error(f"Failed to place order for {symbol}: {e}")
            return None
            
    def get_positions(self) -> List[Dict]:
        """Get current positions"""
        if not self.connected:
            self.logger.error("Not connected to IBKR")
            return []
            
        try:
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
