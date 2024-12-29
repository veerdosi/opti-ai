#!/usr/bin/env python
"""
Quick start test script to validate system functionality
Run this script to test core components of the system
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from backend.data_manager import MarketDataManager, MarketDataConfig
from backend.options_analysis import create_credit_spread, BacktestEngine
from backend.reporting_module import ReportGenerator
from backend.ibkr_integration import create_trading_system

def test_data_management():
    """Test data fetching and management"""
    print("\n1. Testing Data Management...")
    
    dm = MarketDataManager()
    config = MarketDataConfig(
        symbols=['SPY'],
        start_date=datetime.now() - timedelta(days=30),
        end_date=datetime.now(),
        validate_data=True
    )
    
    try:
        data = dm.fetch_historical_data(config)
        print("✓ Historical data fetched successfully")
        print(f"✓ Got {len(data['SPY'])} days of data for SPY")
        
        vol = dm.get_historical_volatility('SPY')
        print(f"✓ Current 30-day volatility: {vol.iloc[-1]:.2%}")
        
    except Exception as e:
        print(f"✗ Error in data management: {str(e)}")
        return False
        
    return True

def test_options_strategy():
    """Test options strategy creation and analysis"""
    print("\n2. Testing Options Strategy...")
    
    try:
        # Create a bull put spread
        strategy = create_credit_spread(
            symbol="SPY",
            expiry=datetime.now() + timedelta(days=30),
            long_strike=400,
            short_strike=410,
            is_call=False
        )
        
        print("✓ Strategy created successfully")
        
        # Calculate Greeks
        greeks = strategy.calculate_greeks(
            current_price=405.0,
            volatility=0.2,
            risk_free_rate=0.03
        )
        
        print("✓ Greeks calculated:")
        for greek, value in greeks.items():
            print(f"  {greek}: {value:.4f}")
            
    except Exception as e:
        print(f"✗ Error in options strategy: {str(e)}")
        return False
        
    return True

def test_backtesting():
    """Test backtesting engine"""
    print("\n3. Testing Backtesting Engine...")
    
    try:
        # Setup components
        dm = MarketDataManager()
        backtest = BacktestEngine()
        
        # Create strategy
        strategy = create_credit_spread(
            symbol="SPY",
            expiry=datetime.now() + timedelta(days=30),
            long_strike=400,
            short_strike=410,
            is_call=False
        )
        
        backtest.add_strategy(strategy)
        
        # Get historical data
        config = MarketDataConfig(
            symbols=["SPY"],
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        
        historical_data = dm.fetch_historical_data(config)
        
        # Run backtest
        results = backtest.run_backtest(
            historical_data=historical_data["SPY"],
            volatility=0.2,
            risk_free_rate=0.03
        )
        
        print("✓ Backtest completed successfully")
        
        # Generate report
        report_gen = ReportGenerator(results)
        report = report_gen.generate_report("Bull Put Spread SPY")
        
        print("\nBacktest Results:")
        print(f"Total Return: {report['summary_statistics']['total_return']:.2f}")
        print(f"Sharpe Ratio: {report['risk_metrics']['sharpe_ratio']:.2f}")
        print(f"Max Drawdown: {report['summary_statistics']['max_drawdown']:.2%}")
        
    except Exception as e:
        print(f"✗ Error in backtesting: {str(e)}")
        return False
        
    return True

def test_trading_system():
    """Test trading system integration"""
    print("\n4. Testing Trading System...")
    
    try:
        # Create and initialize trading system
        trading_system = create_trading_system()
        
        # Add test strategy
        strategy_config = {
            'name': 'Test Bull Put Spread',
            'threshold': 0.01,
            'position_size': 1
        }
        
        trading_system.add_strategy('TestStrategy', strategy_config, ['SPY'])
        
        # Generate signals
        signals = trading_system.generate_trading_signals('TestStrategy')
        print(f"✓ Generated {len(signals)} trading signals")
        
        # Get strategy status
        status = trading_system.get_strategy_status('TestStrategy')
        print("✓ Strategy status retrieved successfully")
        
        # Clean shutdown
        trading_system.shutdown()
        print("✓ Trading system shutdown completed")
        
    except Exception as e:
        print(f"✗ Error in trading system: {str(e)}")
        return False
        
    return True

def main():
    """Run all tests"""
    print("Starting system tests...")
    
    tests = [
        test_data_management,
        test_options_strategy,
        test_backtesting,
        test_trading_system
    ]
    
    results = []
    for test in tests:
        results.append(test())
        
    print("\nTest Summary:")
    print(f"Total Tests: {len(tests)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())
