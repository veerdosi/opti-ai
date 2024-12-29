# OPTI AI

A Python-based system for analyzing options strategies with backtesting capabilities and a React dashboard. Includes Interactive Brokers (IBKR) integration for paper trading.

## Features

- Options strategy analysis and backtesting
- Real-time monitoring dashboard
- Greeks calculation and visualization
- Risk metrics and performance analysis
- IBKR integration for paper trading

## Project Structure

```
src/
├── examples/               # Example scripts
│   ├── quickstart.py
│   └── trading-example.py
├── frontend/              # React frontend
│   ├── dashboard.tsx
│   └── strategy-hook.tsx
└── sys/                   # Core system modules
    ├── config-system.py
    ├── data-manager.py
    ├── ikbr.py
    ├── options-analysis.py
    ├── reporting-module.py
    ├── test-script.py
    └── validation-system.py
```

## Requirements

- Python 3.8+
- Node.js 16+
- Interactive Brokers TWS/Gateway (for paper trading)

## Installation

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Install frontend dependencies:

```bash
cd src/frontend
npm install
```

## Quick Start

1. Run example:

```bash
python src/examples/quickstart.py
```

2. Start dashboard:

```bash
cd src/frontend
npm run dev
```

3. Run tests:

```bash
python src/sys/test-script.py
```

## Configuration

Edit `config.json` to configure database settings, market hours, and risk parameters.

## License

MIT License - see LICENSE file for details.

## Disclaimer

For educational purposes only. Not financial advice.
