import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { supabase } from '../lib/supabase'
import { ServiceStatus, HealthMetric } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { cn } from '../lib/utils'
import { AlertCircle, CheckCircle, AlertTriangle, Activity, Database, Server, BarChart3, Play, StopCircle } from 'lucide-react'

const SERVICE_ICONS = {
  n8n: Server,
  ollama: Activity,
  flowise: BarChart3,
  qdrant: Database,
  neo4j: Database,
  caddy: Server,
  langfuse: BarChart3,
  clickhouse: Database,
  minio: Database,
  postgres: Database,
  searxng: Server,
  dashboard: Activity,
}

interface DockerContainer {
  Id: string
  Names: string[]
  State: {
    Status: string
    Running: boolean
    StartedAt: string
  }
  Image: string
}

export default function Overview() {
  const [dockerContainers, setDockerContainers] = useState<DockerContainer[]>([])
  const [healthMetrics, setHealthMetrics] = useState<HealthMetric[]>([])
  const [totalVulnerabilities, setTotalVulnerabilities] = useState(0)
  const [criticalVulnerabilities, setCriticalVulnerabilities] = useState(0)

  // Fetch Docker container status
  const dockerQuery = useQuery({
    queryKey: ['docker-containers'],
    queryFn: async () => {
      const response = await axios.get('/api/docker/containers')
      return response.data
    },
    staleTime: 30000, // 30 seconds
    refetchInterval: 30000,
  })

  // Fetch Supabase health data
  const supabaseQuery = useQuery({
    queryKey: ['supabase-health'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('system_health')
        .select('*')
        .gte('timestamp', new Date(Date.now() - 5 * 60 * 1000).toISOString()) // Last 5 minutes
      if (error) throw error
      return data
    },
    staleTime: 60000, // 1 minute
  })

  // Fetch vulnerability data
  const vulnerabilitiesQuery = useQuery({
    queryKey: ['trivy-vulnerabilities'],
    queryFn: async () => {
      const response = await axios.get('/api/vulnerabilities/summary')
      return response.data
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  })

  useEffect(() => {
    if (dockerQuery.data) {
      setDockerContainers(dockerQuery.data)
    }
  }, [dockerQuery.data])

  useEffect(() => {
    if (supabaseQuery.data) {
      setHealthMetrics(supabaseQuery.data)
    }
  }, [supabaseQuery.data])

  useEffect(() => {
    if (vulnerabilitiesQuery.data) {
      setTotalVulnerabilities(vulnerabilitiesQuery.data.total)
      setCriticalVulnerabilities(vulnerabilitiesQuery.data.critical)
    }
  }, [vulnerabilitiesQuery.data])

  const getServiceStatus = (containerName: string): ServiceStatus => {
    const container = dockerContainers.find(c => c.Names.some(name => name.includes(containerName)))
    if (!container) {
      return { name: containerName, status: 'down' as const, lastUpdated: new Date() }
    }

    const status = container.State.Running ? 'up' : 'down' as ServiceStatus['status']
    return {
      name: containerName,
      status,
      lastUpdated: new Date(container.State.StartedAt),
    }
  }

  const coreServices = [
    'n8n', 'ollama', 'flowise', 'qdrant', 'neo4j', 'caddy', 
    'langfuse', 'clickhouse', 'minio', 'postgres', 'searxng'
  ]

  const serviceStatuses = coreServices.map(getServiceStatus)
  const upServices = serviceStatuses.filter(s => s.status === 'up').length
  const totalServices = serviceStatuses.length
  const uptimePercentage = totalServices > 0 ? ((upServices / totalServices) * 100).toFixed(1) : 0

  const IconComponent = (name: string) => {
    const Icon = SERVICE_ICONS[name as keyof typeof SERVICE_ICONS] || Server
    return <Icon className="w-4 h-4" />
  }

  const StatusBadge = ({ status }: { status: ServiceStatus['status'] }) => {
    const statusConfig = {
      up: { className: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle },
      down: { className: 'bg-red-100 text-red-800 border-red-200', icon: AlertCircle },
      warning: { className: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertTriangle },
    }

    const config = statusConfig[status]
    const Icon = config.icon

    return (
      <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${config.className}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row gap-6">
        {/* Main Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1">
          <Card className="card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Uptime</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{uptimePercentage}%</div>
              <p className="text-xs text-muted-foreground">
                {upServices} of {totalServices} services running
              </p>
            </CardContent>
          </Card>

          <Card className="card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Critical Vulnerabilities</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold text-red-600`}>{criticalVulnerabilities}</div>
              <p className="text-xs text-muted-foreground">
                {totalVulnerabilities} total vulnerabilities
              </p>
            </CardContent>
          </Card>

          <Card className="card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Users</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">
                +2 from last week
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <Card className="card md:w-80">
          <CardHeader>
            <CardTitle className="text-lg">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors">
              <span>🔄</span>
              <span>Update Images</span>
            </button>
            <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-green-600 rounded-md hover:bg-green-700 transition-colors">
              <span>▶️</span>
              <span>Restart All</span>
            </button>
            <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors">
              <span>📊</span>
              <span>Generate Report</span>
            </button>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Service Status Grid */}
        <Card className="card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Server className="h-5 w-5" />
              <span>Service Status</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {serviceStatuses.map((service, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 border rounded-lg">
                  <div className={`w-3 h-3 rounded-full ${
                    service.status === 'up' ? 'bg-green-500' : 
                    service.status === 'down' ? 'bg-red-500' : 'bg-yellow-500'
                  }`} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {service.name}
                    </p>
                    <p className={`text-xs ${
                      service.status === 'up' ? 'text-green-600' : 
                      service.status === 'down' ? 'text-red-600' : 'text-yellow-600'
                    }`}>
                      {service.status}
                    </p>
                  </div>
                  <StatusBadge status={service.status} />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Activity */}
        <Card className="card">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Recent Activity</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[
                { time: '2 min ago', event: 'n8n workflow executed successfully', status: 'success' },
                { time: '5 min ago', event: 'Ollama model updated', status: 'success' },
                { time: '12 min ago', event: 'Trivy scan completed - 3 critical vulnerabilities', status: 'warning' },
                { time: '23 min ago', event: 'CI/CD pipeline passed', status: 'success' },
                { time: '1 hr ago', event: 'Supabase backup completed', status: 'success' },
              ].map((activity, index) => (
                <div key={index} className="flex items-center space-x-3 p-2 hover:bg-gray-50 rounded">
                  <div className={`w-2 h-2 rounded-full ${
                    activity.status === 'success' ? 'bg-green-500' : 'bg-yellow-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{activity.event}</p>
                    <p className="text-xs text-gray-500">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Performance Charts Section */}
      <Card className="card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Performance Overview</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* CPU Usage */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">CPU Usage (Last 24h)</h3>
              <div className="h-32 bg-gray-50 rounded-lg p-4">
                <div className="flex items-end h-full space-x-2">
                  {[25, 45, 30, 60, 40, 55].map((usage, index) => (
                    <div 
                      key={index} 
                      className="flex-1 bg-primary-600 rounded" 
                      style={{ height: `${usage}%` }}
                    />
                  ))}
                </div>
                <div className="grid grid-cols-6 gap-1 mt-2">
                  {['1h', '3h', '6h', '12h', '18h', '24h'].map((label, index) => (
                    <div key={index} className="text-xs text-center text-gray-500">
                      {label}
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Memory Usage */}
            <div className="space-y-4">
              <h3 className="text-sm font-medium text-gray-900">Memory Usage</h3>
              <div className="space-y-2">
                {[
                  { name: 'Ollama', used: '2.3GB', total: '8GB', percentage: 29 },
                  { name: 'Postgres', used: '1.2GB', total: '4GB', percentage: 30 },
                  { name: 'n8n', used: '450MB', total: '1GB', percentage: 45 },
                  { name: 'Qdrant', used: '800MB', total: '2GB', percentage: 40 },
                ].map((memory, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-sm text-gray-900">{memory.name}</span>
                    <div className="w-32">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-primary-600 h-2 rounded-full" 
                            style={{ width: `${memory.percentage}%` }}
                          />
                        </div>
                        <span className="text-sm font-medium">{memory.percentage}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function StatusBadge({ status }: { status: ServiceStatus['status'] }) {
  const statusConfig = {
    up: { className: 'bg-green-100 text-green-800 border-green-200', icon: CheckCircle },
    down: { className: 'bg-red-100 text-red-800 border-red-200', icon: AlertCircle },
    warning: { className: 'bg-yellow-100 text-yellow-800 border-yellow-200', icon: AlertTriangle },
  }

  const config = statusConfig[status]
  const Icon = config.icon

  return (
    <div className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${config.className}`}>
      <Icon className="w-3 h-3 mr-1" />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </div>
  )
}