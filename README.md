# OPTI AI

A comprehensive options trading and analysis system that combines real-time market data, sophisticated options analytics, and an interactive dashboard for strategy visualization and management.

## Features

### 1. Market Data Integration

- Real-time data fetching via Interactive Brokers (IBKR) API
- Historical data management with SQLite database
- Automated data validation and cleaning
- Support for multiple data sources (IBKR, yfinance)

### 2. Options Analysis Engine

- Greeks calculation (Delta, Gamma, Theta, Vega)
- Strategy P&L simulation
- Risk metrics computation
- Support for common options strategies:
  - Credit/Debit spreads
  - Iron Condors
  - Butterflies
  - Custom strategy builder

### 3. Interactive Dashboard

- Real-time strategy monitoring
- Performance visualization
- Greeks analysis
- Position management
- Risk metrics display

## Installation

1. Clone the repository:

```bash
git clone https://github.com/veerdosi/opti-ai
cd opti_ai
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install required packages:

```bash
pip install -r requirements.txt
```

4. Install frontend dependencies (for the dashboard):

```bash
npm install
```

## Configuration

1. Create a `.env` file in the project root:

```env
IBKR_PORT=7497
IBKR_HOST=127.0.0.1
IBKR_CLIENT_ID=1
DB_PATH=market_data.db
```

2. Configure IBKR TWS or Gateway:

- Enable API connections
- Set up paper trading account for testing

## Testing

Run the system tests:

```bash
python src/test-script.py
```

## Example Usage

1. **Basic Strategy Analysis**:

```python
from src.options_analysis import create_credit_spread
from src.data_manager import MarketDataManager

# Create and analyze a strategy
strategy = create_credit_spread("SPY", expiry="2024-02-15", strikes=[400, 410])
```

2. **Run Trading Example**:

```bash
python src/trading-example.py
```

## Disclaimer

This software is for educational purposes only. Always perform your own due diligence before trading options or any financial instruments. The authors take no responsibility for financial losses incurred using this software.

## License

MIT License
