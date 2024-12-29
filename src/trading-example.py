def run_trading_example():
    # Initialize the trading system
    trading_system = create_trading_system()
    
    try:
        # Define a simple options strategy
        strategy_config = {
            'name': 'Bull Put Spread SPY',
            'threshold': 0.01,  # 1% price movement threshold
            'position_size': 1,
            'max_positions': 3
        }
        
        # Add strategy to the system
        trading_system.add_strategy('BullPutSpread', strategy_config, ['SPY'])
        
        # Monitor the strategy for a period
        monitoring_period = 60  # seconds
        start_time = time.time()
        
        while time.time() - start_time < monitoring_period:
            # Generate and process trading signals
            signals = trading_system.generate_trading_signals('BullPutSpread')
            
            for signal in signals:
                # Execute paper trades based on signals
                order_id = trading_system.execute_paper_trade(
                    'BullPutSpread',
                    signal['symbol'],
                    signal['quantity']
                )
                
                if order_id:
                    print(f"Executed trade: {signal}")
            
            # Get and print strategy status
            status = trading_system.get_strategy_status('BullPutSpread')
            print(f"\nStrategy Status:\n{json.dumps(status, indent=2)}")
            
            # Sleep for a short period
            time.sleep(5)
            
    finally:
        # Clean shutdown
        trading_system.shutdown()

if __name__ == "__main__":
    run_trading_example()