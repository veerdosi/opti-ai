import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ArrowUpCircle, ArrowDownCircle, Activity, DollarSign } from 'lucide-react';

const OptionsDashboard = () => {
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [timeframe, setTimeframe] = useState('1D');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Mock data - replace with actual API calls
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Simulate API call
        const mockStrategies = [
          {
            name: "Bull Put Spread SPY",
            type: "Credit Spread",
            pnl: generateMockPnLData(),
            greeks: {
              delta: 0.45,
              gamma: 0.02,
              theta: -0.15,
              vega: 0.30
            },
            performance: {
              totalReturn: 15.5,
              sharpeRatio: 1.8,
              maxDrawdown: -5.2,
              winRate: 65
            },
            positions: [
              { symbol: "SPY", type: "Long Put", strike: 400, expiry: "2024-02-15" },
              { symbol: "SPY", type: "Short Put", strike: 410, expiry: "2024-02-15" }
            ]
          },
          // Add more strategies here
        ];

        setStrategies(mockStrategies);
        setActiveStrategy(mockStrategies[0]);
        setIsLoading(false);
      } catch (err) {
        setError("Failed to fetch strategy data");
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const generateMockPnLData = () => {
    return Array.from({ length: 30 }, (_, i) => ({
      date: new Date(2024, 0, i + 1).toISOString().split('T')[0],
      value: Math.random() * 1000 - 500,
      cumulative: Math.random() * 2000 - 1000
    }));
  };

  if (isLoading) return (
    <div className="flex items-center justify-center h-64">
      <Activity className="animate-spin h-8 w-8 text-blue-500" />
    </div>
  );

  if (error) return (
    <Alert variant="destructive">
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  );

  if (!activeStrategy) return null;

  return (
    <div className="p-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Options Analysis Dashboard</h1>
        <div className="flex gap-2">
          {['1D', '1W', '1M', '3M', 'YTD'].map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className={`px-3 py-1 rounded ${
                timeframe === tf ? 'bg-blue-500 text-white' : 'bg-gray-100'
              }`}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {/* Strategy Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {strategies.map((strategy) => (
          <Card 
            key={strategy.name}
            className={`cursor-pointer hover:shadow-lg transition-shadow ${
              activeStrategy?.name === strategy.name ? 'border-blue-500 border-2' : ''
            }`}
            onClick={() => setActiveStrategy(strategy)}
          >
            <CardHeader>
              <CardTitle className="flex justify-between items-center">
                {strategy.name}
                {strategy.performance.totalReturn > 0 ? (
                  <ArrowUpCircle className="text-green-500" />
                ) : (
                  <ArrowDownCircle className="text-red-500" />
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600">{strategy.type}</p>
              <p className={`text-lg font-bold ${
                strategy.performance.totalReturn > 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {strategy.performance.totalReturn > 0 ? '+' : ''}
                {strategy.performance.totalReturn.toFixed(2)}%
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="greeks">Greeks</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
          <TabsTrigger value="positions">Positions</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* P&L Chart */}
            <Card className="col-span-2">
              <CardHeader>
                <CardTitle>Strategy Performance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={activeStrategy.pnl}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Area 
                        type="monotone" 
                        dataKey="cumulative" 
                        stroke="#8884d8" 
                        fill="#8884d8" 
                        fillOpacity={0.3}
                        name="Cumulative P&L" 
                      />
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#82ca9d" 
                        fill="#82ca9d"
                        fillOpacity={0.3}
                        name="Daily P&L" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Key Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Key Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Total Return</p>
                    <p className="text-2xl font-bold">
                      {activeStrategy.performance.totalReturn.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Sharpe Ratio</p>
                    <p className="text-2xl font-bold">
                      {activeStrategy.performance.sharpeRatio.toFixed(2)}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Max Drawdown</p>
                    <p className="text-2xl font-bold">
                      {activeStrategy.performance.maxDrawdown.toFixed(2)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Win Rate</p>
                    <p className="text-2xl font-bold">
                      {activeStrategy.performance.winRate}%
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="greeks">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Greeks Display */}
            <Card>
              <CardHeader>
                <CardTitle>Option Greeks</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6">
                  {Object.entries(activeStrategy.greeks).map(([greek, value]) => (
                    <div key={greek} className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-lg font-semibold capitalize">{greek}</p>
                      <p className="text-3xl font-bold text-blue-600">
                        {value.toFixed(3)}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Greeks Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Greeks History</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={activeStrategy.pnl}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="delta" stroke="#8884d8" name="Delta" />
                      <Line type="monotone" dataKey="gamma" stroke="#82ca9d" name="Gamma" />
                      <Line type="monotone" dataKey="theta" stroke="#ffc658" name="Theta" />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="performance">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Performance Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Sharpe Ratio</span>
                    <span className="font-bold">{activeStrategy.performance.sharpeRatio.toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Max Drawdown</span>
                    <span className="font-bold text-red-500">
                      {activeStrategy.performance.maxDrawdown.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Win Rate</span>
                    <span className="font-bold">{activeStrategy.performance.winRate}%</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Return Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Return Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={activeStrategy.pnl}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Area 
                        type="monotone" 
                        dataKey="value" 
                        stroke="#82ca9d"
                        fill="#82ca9d" 
                        fillOpacity={0.3}
                        name="Daily Returns" 
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="positions">
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
                      <th className="text-left p-2">Strike</th>
                      <th className="text-left p-2">Expiry</th>
                      <th className="text-right p-2">P&L</th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeStrategy.positions.map((position, index) => (
                      <tr key={index} className="border-b">
                        <td className="p-2">{position.symbol}</td>
                        <td className="p-2">{position.type}</td>
                        <td className="p-2">${position.strike}</td>
                        <td className="p-2">{position.expiry}</td>
                        <td className="p-2 text-right">
                          <span className={position.type.includes('Long') ? 'text-green-500' : 'text-red-500'}>
                            {position.type.includes('Long') ? '+' : '-'}$100
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default OptionsDashboard;
                  