// hooks/useStrategyData.ts
import { useState, useEffect } from 'react';
import Papa from 'papaparse';

interface Position {
  symbol: string;
  type: string;
  quantity: number;
  pnl: number;
  entryPrice: number;
  currentPrice: number;
}

interface Greeks {
  delta: number;
  gamma: number;
  theta: number;
  vega: number;
}

interface Performance {
  totalReturn: number;
  sharpeRatio: number;
  maxDrawdown: number;
  winRate: number;
  profitFactor: number;
  dailyReturns: number[];
}

interface Strategy {
  name: string;
  type: string;
  performance: Performance;
  greeks: Greeks;
  positions: Position[];
  historicalData: Array<{
    date: string;
    value: number;
    pnl: number;
  }>;
}

interface UseStrategyDataReturn {
  strategies: Strategy[];
  activeStrategy: Strategy | null;
  setActiveStrategy: (strategy: Strategy) => void;
  isLoading: boolean;
  error: string | null;
  refreshData: () => Promise<void>;
  filterStrategies: (filter: string) => void;
  getStrategyMetrics: (strategyName: string) => any;
}

export const useStrategyData = (): UseStrategyDataReturn => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [filteredStrategies, setFilteredStrategies] = useState<Strategy[]>([]);
  const [activeStrategy, setActiveStrategy] = useState<Strategy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const processStrategyData = (rawData: any[]): Strategy[] => {
    const strategyGroups = rawData.reduce((acc, record) => {
      if (!acc[record.strategy]) {
        acc[record.strategy] = [];
      }
      acc[record.strategy].push(record);
      return acc;
    }, {} as Record<string, any[]>);

    return Object.entries(strategyGroups).map(([name, data]) => ({
      name,
      type: data[0].type || "Options Strategy",
      performance: calculatePerformance(data),
      greeks: calculateGreeks(data),
      positions: extractPositions(data),
      historicalData: processHistoricalData(data)
    }));
  };

  const calculatePerformance = (data: any[]): Performance => {
    const returns = data.map(d => d.pnl || 0);
    const totalReturn = returns.reduce((a, b) => a + b, 0);
    const positiveReturns = returns.filter(r => r > 0);
    const negativeReturns = returns.filter(r => r < 0);
    
    return {
      totalReturn,
      sharpeRatio: calculateSharpeRatio(returns),
      maxDrawdown: calculateMaxDrawdown(returns),
      winRate: (positiveReturns.length / returns.length) * 100,
      profitFactor: Math.abs(
        positiveReturns.reduce((a, b) => a + b, 0) / 
        (negativeReturns.reduce((a, b) => a + b, 0) || 1)
      ),
      dailyReturns: returns
    };
  };

  const calculateSharpeRatio = (returns: number[]): number => {
    const riskFreeRate = 0.02; // Assuming 2% risk-free rate
    const avg = returns.reduce((a, b) => a + b, 0) / returns.length;
    const excessReturns = avg - (riskFreeRate / 252); // Daily risk-free rate
    const std = Math.sqrt(
      returns.reduce((a, b) => a + Math.pow(b - avg, 2), 0) / returns.length
    );
    return (std === 0) ? 0 : (excessReturns / std) * Math.sqrt(252); // Annualized
  };

  const calculateMaxDrawdown = (returns: number[]): number => {
    let maxDrawdown = 0;
    let peak = 0;
    let cumulativeReturn = 0;

    returns.forEach(ret => {
      cumulativeReturn += ret;
      if (cumulativeReturn > peak) {
        peak = cumulativeReturn;
      }
      const drawdown = (peak - cumulativeReturn) / (1 + peak);
      maxDrawdown = Math.max(maxDrawdown, drawdown);
    });

    return maxDrawdown;
  };

  const calculateGreeks = (data: any[]): Greeks => {
    const latest = data[data.length - 1];
    const greeks: Greeks = {
      delta: latest.delta || 0,
      gamma: latest.gamma || 0,
      theta: latest.theta || 0,
      vega: latest.vega || 0
    };

    // Apply position size weighting to Greeks
    const positionSize = latest.position_size || 1;
    return Object.entries(greeks).reduce((acc, [key, value]) => ({
      ...acc,
      [key]: value * positionSize
    }), {} as Greeks);
  };

  const extractPositions = (data: any[]): Position[] => {
    const activePositions = data.filter(d => d.position_active);
    const latestData = activePositions[activePositions.length - 1] || {};

    return activePositions.map(d => ({
      symbol: d.symbol,
      type: d.position_type,
      quantity: d.quantity,
      pnl: d.position_pnl || 0,
      entryPrice: d.entry_price || 0,
      currentPrice: latestData.price || d.entry_price || 0
    }));
  };

  const processHistoricalData = (data: any[]) => {
    return data.map(d => ({
      date: d.date,
      value: d.portfolio_value || 0,
      pnl: d.pnl || 0
    })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  };

  const fetchData = async () => {
    try {
      setIsLoading(true);
      const response = await window.fs.readFile('market_data.db');
      const content = new TextDecoder().decode(response);

      Papa.parse(content, {
        header: true,
        dynamicTyping: true,
        complete: (results) => {
          const processedStrategies = processStrategyData(results.data);
          setStrategies(processedStrategies);
          setFilteredStrategies(processedStrategies);
          if (!activeStrategy && processedStrategies.length > 0) {
            setActiveStrategy(processedStrategies[0]);
          }
          setIsLoading(false);
        },
        error: (error) => {
          setError("Failed to parse data");
          setIsLoading(false);
        }
      });
    } catch (err) {
      setError("Failed to fetch data");
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filterStrategies = (filter: string) => {
    const filtered = strategies.filter(strategy => 
      strategy.name.toLowerCase().includes(filter.toLowerCase()) ||
      strategy.type.toLowerCase().includes(filter.toLowerCase())
    );
    setFilteredStrategies(filtered);
  };

  const getStrategyMetrics = (strategyName: string) => {
    const strategy = strategies.find(s => s.name === strategyName);
    if (!strategy) return null;

    return {
      performance: strategy.performance,
      positions: strategy.positions,
      greeks: strategy.greeks,
      historicalData: strategy.historicalData
    };
  };

  const refreshData = async () => {
    await fetchData();
  };

  return {
    strategies: filteredStrategies,
    activeStrategy,
    setActiveStrategy,
    isLoading,
    error,
    refreshData,
    filterStrategies,
    getStrategyMetrics
  };
};

export default useStrategyData;
