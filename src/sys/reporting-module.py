from dataclasses import dataclass
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

@dataclass
class RiskMetrics:
    var_95: float  # 95% Value at Risk
    var_99: float  # 99% Value at Risk
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

@dataclass
class PerformanceAttribution:
    delta_pnl: float
    gamma_pnl: float
    theta_pnl: float
    vega_pnl: float
    total_pnl: float
    
class ReportGenerator:
    def __init__(self, strategy_results: pd.DataFrame):
        """
        Initialize with strategy backtest results
        strategy_results should contain columns: date, pnl, delta, gamma, theta, vega
        """
        self.results = strategy_results
        self.risk_free_rate = 0.03  # Configurable risk-free rate
        
    def calculate_risk_metrics(self) -> RiskMetrics:
        """Calculate comprehensive risk metrics for the strategy"""
        returns = self.results['pnl'].pct_change().dropna()
        
        # Calculate Value at Risk
        var_95 = np.percentile(returns, 5)
        var_99 = np.percentile(returns, 1)
        
        # Calculate Sharpe Ratio
        excess_returns = returns - (self.risk_free_rate / 252)  # Daily risk-free rate
        sharpe = np.sqrt(252) * excess_returns.mean() / returns.std()
        
        # Calculate Sortino Ratio
        downside_returns = returns[returns < 0]
        sortino = np.sqrt(252) * excess_returns.mean() / downside_returns.std()
        
        # Calculate Maximum Drawdown
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdowns = cumulative / running_max - 1
        max_drawdown = drawdowns.min()
        
        # Calculate Win Rate and Profit Factor
        wins = len(returns[returns > 0])
        total_trades = len(returns)
        win_rate = wins / total_trades if total_trades > 0 else 0
        
        profit_factor = (
            abs(returns[returns > 0].sum()) / 
            abs(returns[returns < 0].sum())
            if len(returns[returns < 0]) > 0 else float('inf')
        )
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor
        )
    
    def calculate_performance_attribution(self) -> PerformanceAttribution:
        """Calculate P&L attribution to different risk factors"""
        # Calculate daily changes in underlying and Greeks
        delta_changes = self.results['delta'].diff()
        gamma_changes = self.results['gamma'].diff()
        price_changes = self.results['price'].diff()
        
        # Attribution calculations
        delta_pnl = (self.results['delta'] * price_changes).sum()
        gamma_pnl = (0.5 * self.results['gamma'] * price_changes**2).sum()
        theta_pnl = self.results['theta'].sum() / 252  # Daily theta
        vega_pnl = (self.results['vega'] * self.results['implied_volatility'].diff()).sum()
        
        total_pnl = self.results['pnl'].sum()
        
        return PerformanceAttribution(
            delta_pnl=delta_pnl,
            gamma_pnl=gamma_pnl,
            theta_pnl=theta_pnl,
            vega_pnl=vega_pnl,
            total_pnl=total_pnl
        )
    
    def generate_report(self, strategy_name: str) -> Dict:
        """Generate comprehensive strategy report"""
        risk_metrics = self.calculate_risk_metrics()
        performance_attr = self.calculate_performance_attribution()
        
        report = {
            "strategy_name": strategy_name,
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary_statistics": {
                "total_return": self.results['pnl'].sum(),
                "annualized_return": self.results['pnl'].mean() * 252,
                "annualized_volatility": self.results['pnl'].std() * np.sqrt(252),
                "max_drawdown": risk_metrics.max_drawdown,
            },
            "risk_metrics": {
                "var_95": risk_metrics.var_95,
                "var_99": risk_metrics.var_99,
                "sharpe_ratio": risk_metrics.sharpe_ratio,
                "sortino_ratio": risk_metrics.sortino_ratio,
                "win_rate": risk_metrics.win_rate,
                "profit_factor": risk_metrics.profit_factor
            },
            "performance_attribution": {
                "delta_contribution": performance_attr.delta_pnl,
                "gamma_contribution": performance_attr.gamma_pnl,
                "theta_contribution": performance_attr.theta_pnl,
                "vega_contribution": performance_attr.vega_pnl,
                "total_pnl": performance_attr.total_pnl
            },
            "position_summary": self._generate_position_summary(),
            "risk_decomposition": self._generate_risk_decomposition()
        }
        
        return report
    
    def _generate_position_summary(self) -> Dict:
        """Generate summary of current positions"""
        latest = self.results.iloc[-1]
        return {
            "delta_exposure": latest['delta'],
            "gamma_exposure": latest['gamma'],
            "theta_exposure": latest['theta'],
            "vega_exposure": latest['vega'],
            "current_pnl": latest['pnl']
        }
    
    def _generate_risk_decomposition(self) -> Dict:
        """Generate risk decomposition analysis"""
        returns = self.results['pnl'].pct_change().dropna()
        
        return {
            "daily_var_contribution": {
                "delta": (self.results['delta'] ** 2).mean(),
                "gamma": (self.results['gamma'] ** 2).mean(),
                "theta": (self.results['theta'] ** 2).mean(),
                "vega": (self.results['vega'] ** 2).mean()
            },
            "correlation_matrix": self.results[['delta', 'gamma', 'theta', 'vega']].corr().to_dict()
        }
