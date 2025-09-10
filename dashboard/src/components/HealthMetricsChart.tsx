import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { cn } from '../lib/utils'
import { TrendingUp, TrendingDown, AlertTriangle, BarChart3 } from 'lucide-react'

interface MetricPoint {
  timestamp: string
  value: number
  service?: string
}

interface HealthData {
  cpu: MetricPoint[]
  memory: MetricPoint[]
  responseTime: MetricPoint[]
}

export function HealthMetricsChart() {
  const [selectedMetric, setSelectedMetric] = useState<'cpu' | 'memory' | 'responseTime'>('cpu')
  const [timeRange, setTimeRange] = useState<'1h' | '6h' | '24h'>('6h')

  const { data: healthData, isLoading, error } = useQuery<HealthData>({
    queryKey: ['health-metrics', selectedMetric, timeRange],
    queryFn: async () => {
      const response = await axios.get(`/api/metrics/health?metric=${selectedMetric}&range=${timeRange}`)
      return response.data
    },
    refetchInterval: 30000, // 30 seconds
    staleTime: 30000,
  })

  const chartData = healthData ? healthData[selectedMetric] : []
  
  const formatTime = (tickItem: string) => {
    const date = new Date(tickItem)
    const now = new Date()
    const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (timeRange === '1h') {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    } else if (timeRange === '6h') {
      return date.getHours() + ':00'
    } else {
      return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
    }
  }

  const getMetricLabel = (metric: string) => {
    switch (metric) {
      case 'cpu': return 'CPU Usage (%)'
      case 'memory': return 'Memory Usage (MB)'
      case 'responseTime': return 'Response Time (ms)'
      default: return metric
    }
  }

  const getTrendIndicator = () => {
    if (!chartData || chartData.length < 2) return null
    
    const first = chartData[0].value
    const last = chartData[chartData.length - 1].value
    const change = ((last - first) / first * 100)
    
    if (Math.abs(change) < 1) return null
    
    const changeFormatted = change.toFixed(1)
    const isPositive = change > 0
    
    return (
      <div className={cn(
        "flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium",
        isPositive ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
      )}>
        {isPositive ? (
          <TrendingUp className="w-3 h-3" />
        ) : (
          <TrendingDown className="w-3 h-3" />
        )}
        <span>{isPositive ? '+' : ''}{changeFormatted}%</span>
      </div>
    )
  }

  const MetricButton = ({ 
    metric, 
    label, 
    active, 
    onClick 
  }: { 
    metric: 'cpu' | 'memory' | 'responseTime'
    label: string
    active: boolean
    onClick: () => void
  }) => (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 rounded-md text-xs font-medium transition-colors border",
        active 
          ? "bg-primary-100 text-primary-700 border-primary-200" 
          : "text-muted-foreground border-gray-200 hover:bg-gray-50 hover:border-gray-300"
      )}
    >
      {label}
    </button>
  )

  const TimeRangeButton = ({ 
    range, 
    label, 
    active, 
    onClick 
  }: { 
    range: '1h' | '6h' | '24h'
    label: string
    active: boolean
    onClick: () => void
  }) => (
    <button
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 rounded-md text-xs font-medium transition-colors border",
        active 
          ? "bg-primary-100 text-primary-700 border-primary-200" 
          : "text-muted-foreground border-gray-200 hover:bg-gray-50 hover:border-gray-300"
      )}
    >
      {label}
    </button>
  )

  if (isLoading) {
    return (
      <Card className="card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Health Metrics</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="h-80 flex items-center justify-center">
          <div className="animate-pulse space-y-4 w-full">
            <div className="h-64 bg-gray-200 rounded-lg"></div>
            <div className="flex space-x-2">
              <div className="h-8 bg-gray-200 rounded w-20"></div>
              <div className="h-8 bg-gray-200 rounded w-20"></div>
              <div className="h-8 bg-gray-200 rounded w-20"></div>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="card border-red-200">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2 text-red-600">
            <AlertTriangle className="h-5 w-5" />
            <span>Metrics Unavailable</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="text-red-600 space-y-2">
          <p className="text-sm">Failed to load health metrics</p>
          <p className="text-xs opacity-75">Check Docker metrics service or try refreshing</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="card">
      <CardHeader className="pb-4">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Health Metrics</span>
          </CardTitle>
          
          <div className="flex flex-wrap gap-2">
            <TimeRangeButton
              range="1h"
              label="1h"
              active={timeRange === '1h'}
              onClick={() => setTimeRange('1h')}
            />
            <TimeRangeButton
              range="6h"
              label="6h"
              active={timeRange === '6h'}
              onClick={() => setTimeRange('6h')}
            />
            <TimeRangeButton
              range="24h"
              label="24h"
              active={timeRange === '24h'}
              onClick={() => setTimeRange('24h')}
            />
          </div>
        </div>
        
        <div className="flex flex-wrap gap-2 pt-2">
          <MetricButton
            metric="cpu"
            label="CPU"
            active={selectedMetric === 'cpu'}
            onClick={() => setSelectedMetric('cpu')}
          />
          <MetricButton
            metric="memory"
            label="Memory"
            active={selectedMetric === 'memory'}
            onClick={() => setSelectedMetric('memory')}
          />
          <MetricButton
            metric="responseTime"
            label="Response"
            active={selectedMetric === 'responseTime'}
            onClick={() => setSelectedMetric('responseTime')}
          />
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-gray-900">
              {getMetricLabel(selectedMetric)}
            </h3>
            {getTrendIndicator()}
          </div>
          
          {chartData.length > 0 ? (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                  <XAxis 
                    dataKey="timestamp" 
                    tickFormatter={formatTime}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    interval="preserveStartEnd"
                    minTickGap={20}
                  />
                  <YAxis 
                    tickLine={false}
                    axisLine={false}
                    tick={{ fontSize: 11, fill: '#64748b' }}
                    tickFormatter={(value) => `${value}`}
                    domain={['auto', 'auto']}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'white',
                      border: '1px solid #e2e8f0',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                    labelFormatter={formatTime}
                    formatter={(value: number) => [value.toFixed(1), getMetricLabel(selectedMetric)]}
                  />
                  <Legend verticalAlign="top" height={36} />
                  <Line 
                    type="monotone" 
                    dataKey="value" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    dot={{ 
                      fill: '#3b82f6', 
                      stroke: 'white', 
                      strokeWidth: 2, 
                      r: 4,
                      fillOpacity: 0.8
                    }}
                    activeDot={{ 
                      r: 6, 
                      stroke: '#3b82f6', 
                      strokeWidth: 2,
                      fillOpacity: 1
                    }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-80 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
              <div className="text-center text-muted-foreground">
                <BarChart3 className="h-12 w-12 mx-auto mb-4 opacity-40" />
                <h3 className="text-sm font-medium mb-1">No Data Available</h3>
                <p className="text-xs">No metrics found for the selected time range</p>
                <p className="text-xs mt-1">Try adjusting the time range or metric type</p>
              </div>
            </div>
          )}
        </div>
        
        {/* Data Summary */}
        {chartData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {Math.max(...chartData.map(d => d.value)).toFixed(1)}
              </div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide">Peak</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {chartData[chartData.length - 1]?.value.toFixed(1) || '0'}
              </div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide">Current</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-primary-600">
                {chartData.length}
              </div>
              <div className="text-xs text-muted-foreground uppercase tracking-wide">Data Points</div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}