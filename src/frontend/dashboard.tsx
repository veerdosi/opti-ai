import React, { useState } from 'react';
import { useStrategyData } from './strategy-hook';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

// Sub-components
const StrategyCard = ({ strategy, isActive, onClick }) => (
  <Card 
    className={`cursor-pointer hover:shadow-lg transition-shadow ${
      isActive ? 'border-blue-500 border-2' : ''
    }`}
    onClick={onClick}
  >
    <CardHeader>
      <CardTitle>{strategy.name}</CardTitle>
    </CardHeader>
    <CardContent>
      <p className="text-sm text-gray-600">{strategy.type}</p>
      <p className={`text-lg font-bold ${
        strategy.performance.totalReturn > 0 ? 'text-green-500' : 'text-red-500'
      }`}>
        {strategy.performance.totalReturn.toFixed(2)}%
      </p>
      <div className="mt-2 grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="text-gray-500">Sharpe:</span>
          <span className="ml-1">{strategy.performance.sharpeRatio.toFixed(2)}</span>
        </div>
        <div>
          <span className="text-gray-500">Win Rate:</span>
          <span className="ml-1">{(strategy.performance.winRate).toFixed(1)}%</span>
        </div>
      </div>
    </CardContent>
  </Card>
);

const PerformancePanel = ({ data }) => (
  <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
    <Card className="lg:col-span-2">
      <CardHeader>
        <CardTitle>Performance Overview</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data.historicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#8884d8" name="P&L" />
              <Line type="monotone" dataKey="pnl" stroke="#82ca9d" name="Daily P&L" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
    <Card>
      <CardHeader>
        <CardTitle>Key Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-between">
            <span className="text-gray-500">Total Return</span>
            <span className={`font-bold ${data.totalReturn >= 0 ? 'text-green-500' : 'text-red-500'}`}>
              {data.totalReturn.toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Sharpe Ratio</span>
            <span className="font-bold">{data.sharpeRatio.toFixed(2)}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Max Drawdown</span>
            <span className="font-bold text-red-500">
              {(data.maxDrawdown * 100).toFixed(2)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Win Rate</span>
            <span className="font-bold">{(data.winRate).toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">Profit Factor</span>
            <span className="font-bold">{data.profitFactor.toFixed(2)}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  </div>
);

const GreeksPanel = ({ greeks }) => (
  <Card>
    <CardHeader>
      <CardTitle>Option Greeks</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="grid grid-cols-2 gap-4">
        {Object.entries(greeks).map(([greek, value]) => (
          <div key={greek} className="p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-500 capitalize">{greek}</p>
            <p className="text-2xl font-bold">{value.toFixed(3)}</p>
          </div>
        ))}
      </div>
    </CardContent>
  </Card>
);

const PositionsPanel = ({ positions }) => (
  <Card>
    <CardHeader>
      <CardTitle>Current Positions</CardTitle>
    </CardHeader>
    <CardContent>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Symbol</th>
              <th className="text-left p-2">Type</th>
              <th className="text-right p-2">Quantity</th>
              <th className="text-right p-2">Entry</th>
              <th className="text-right p-2">Current</th>
              <th className="text-right p-2">P&L</th>
            </tr>
          </thead>
          <tbody>
            {positions.map((position, index) => (
              <tr key={index} className="border-b">
                <td className="p-2">{position.symbol}</td>
                <td className="p-2">{position.type}</td>
                <td className="p-2 text-right">{position.quantity}</td>
                <td className="p-2 text-right">${position.entryPrice.toFixed(2)}</td>
                <td className="p-2 text-right">${position.currentPrice.toFixed(2)}</td>
                <td className="p-2 text-right">
                  <span className={position.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                    {position.pnl >= 0 ? '+' : ''}{position.pnl.toFixed(2)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </CardContent>
  </Card>
);

// Main Dashboard Component
const Dashboard = () => {
  const { 
    strategies, 
    activeStrategy,
    setActiveStrategy,
    isLoading,
    error,
    refreshData,
    filterStrategies
  } = useStrategyData();

  const [searchTerm, setSearchTerm] = useState('');

  const handleSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setSearchTerm(value);
    filterStrategies(value);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Activity className="animate-spin h-8 w-8 text-blue-500" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Options Analysis Dashboard</h1>
        <div className="flex gap-4">
          <Input
            type="text"
            placeholder="Search strategies..."
            value={searchTerm}
            onChange={handleSearch}
            className="w-64"
          />
          <Button onClick={refreshData}>
            Refresh Data
          </Button>
        </div>
      </div>

      {/* Strategy Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map(strategy => (
          <StrategyCard
            key={strategy.name}
            strategy={strategy}
            isActive={activeStrategy?.name === strategy.name}
            onClick={() => setActiveStrategy(strategy)}
          />
        ))}
      </div>

      {/* Strategy Details */}
      {activeStrategy && (
        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="greeks">Greeks</TabsTrigger>
            <TabsTrigger value="positions">Positions</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <PerformancePanel data={activeStrategy.performance} />
          </TabsContent>

          <TabsContent value="greeks">
            <GreeksPanel greeks={activeStrategy.greeks} />
          </TabsContent>

          <TabsContent value="positions">
            <PositionsPanel positions={activeStrategy.positions} />
          </TabsContent>
        </Tabs>
      )}

      {strategies.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500">No strategies found</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;