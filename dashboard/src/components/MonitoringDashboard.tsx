import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { RefreshCw, AlertCircle, CheckCircle2, XCircle, Clock } from 'lucide-react';

interface ServiceStatus {
  name: string;
  status: 'up' | 'down' | 'degraded';
  responseTime: number;
  lastChecked: string;
  uptime: number;
}

interface Metric {
  timestamp: string;
  value: number;
}

interface Alert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  service: string;
}

export function MonitoringDashboard() {
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [metrics, setMetrics] = useState<Record<string, Metric[]>>({});
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchServices = async () => {
    try {
      // In a real implementation, replace with actual API calls
      const mockServices: ServiceStatus[] = [
        {
          name: 'API Service',
          status: 'up',
          responseTime: 42,
          lastChecked: new Date().toISOString(),
          uptime: 99.98,
        },
        {
          name: 'Database',
          status: 'up',
          responseTime: 12,
          lastChecked: new Date().toISOString(),
          uptime: 99.99,
        },
        {
          name: 'Cache',
          status: 'degraded',
          responseTime: 5,
          lastChecked: new Date().toISOString(),
          uptime: 99.5,
        },
      ];
      setServices(mockServices);
    } catch (error) {
      console.error('Error fetching services:', error);
    }
  };

  const fetchMetrics = async () => {
    try {
      // In a real implementation, replace with actual API calls
      const now = new Date();
      const mockMetrics: Record<string, Metric[]> = {
        'CPU Usage': Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(now.getTime() - (23 - i) * 3600000).toISOString(),
          value: Math.floor(Math.random() * 30) + 20,
        })),
        'Memory Usage': Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(now.getTime() - (23 - i) * 3600000).toISOString(),
          value: Math.floor(Math.random() * 20) + 50,
        })),
        'Request Latency': Array.from({ length: 24 }, (_, i) => ({
          timestamp: new Date(now.getTime() - (23 - i) * 3600000).toISOString(),
          value: Math.floor(Math.random() * 100) + 50,
        })),
      };
      setMetrics(mockMetrics);
    } catch (error) {
      console.error('Error fetching metrics:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      // In a real implementation, replace with actual API calls
      const mockAlerts: Alert[] = [
        {
          id: '1',
          severity: 'warning',
          message: 'High CPU usage on worker-1',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          service: 'worker-1',
        },
        {
          id: '2',
          severity: 'critical',
          message: 'Database connection timeout',
          timestamp: new Date(Date.now() - 7200000).toISOString(),
          service: 'database',
        },
      ];
      setAlerts(mockAlerts);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  };

  const refreshAll = async () => {
    setIsLoading(true);
    await Promise.all([fetchServices(), fetchMetrics(), fetchAlerts()]);
    setLastUpdated(new Date().toLocaleTimeString());
    setIsLoading(false);
  };

  useEffect(() => {
    refreshAll();
    // Set up polling
    const interval = setInterval(refreshAll, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'up':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'degraded':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'down':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getAlertColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 border-red-500 text-red-900';
      case 'warning':
        return 'bg-yellow-100 border-yellow-500 text-yellow-900';
      default:
        return 'bg-blue-100 border-blue-500 text-blue-900';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">System Monitoring</h2>
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-500">
            Last updated: {lastUpdated || 'Never'}
          </span>
          <Button variant="outline" size="sm" onClick={refreshAll} disabled={isLoading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {services.map((service) => (
          <Card key={service.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{service.name}</CardTitle>
              {getStatusIcon(service.status)}
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {service.status === 'up' ? 'Operational' : service.status === 'degraded' ? 'Degraded' : 'Down'}
              </div>
              <p className="text-xs text-gray-500">
                Response time: {service.responseTime}ms
              </p>
              <p className="text-xs text-gray-500">
                Uptime: {service.uptime.toFixed(2)}%
              </p>
              <p className="text-xs text-gray-500">
                Last checked: {new Date(service.lastChecked).toLocaleString()}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>System Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(metrics).map(([metricName, data]) => (
                <div key={metricName} className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{metricName}</span>
                    <span className="text-gray-500">{data[data.length - 1]?.value}%</span>
                  </div>
                  <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${data[data.length - 1]?.value}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
          </CardHeader>
          <CardContent>
            {alerts.length > 0 ? (
              <div className="space-y-2">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 rounded border ${getAlertColor(alert.severity)}`}
                  >
                    <div className="flex justify-between">
                      <span className="font-medium">{alert.service}</span>
                      <span className="text-xs">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-sm">{alert.message}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500">No recent alerts</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Service Logs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64 overflow-y-auto bg-black text-green-400 font-mono text-sm p-4 rounded">
              {Array.from({ length: 20 }).map((_, i) => (
                <div key={i} className="whitespace-nowrap">
                  [{new Date().toLocaleTimeString()}] INFO: This is a sample log message #{i + 1}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
