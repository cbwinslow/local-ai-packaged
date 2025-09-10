import { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios, { AxiosError } from 'axios'
import { supabase } from '../lib/supabase'
import { ServiceStatus, HealthMetric } from '../types'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { cn } from '../lib/utils'
import { AlertCircle, CheckCircle, AlertTriangle, Activity, Database, Server, BarChart3, Play, RefreshCw, Search } from 'lucide-react'

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

type CoreService = {
  readonly name: string
  readonly display: string
  readonly priority: number
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
      const { data, error } = await axios.get('/api/docker/containers')
      if (error) {
        console.error('Docker API error:', error)
        throw new Error('Failed to fetch container status')
      }
      return data
    },
    staleTime: 30000,
    refetchInterval: 30000,
    retry: 2,
    onError: (error: AxiosError | unknown) => {
      console.error('Docker query failed:', error)
    }
  })

  // Fetch Supabase health data with real-time subscription preparation
  const supabaseQuery = useQuery({
    queryKey: ['supabase-health'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('system_health')
        .select('*')
        .gte('timestamp', new Date(Date.now() - 5 * 60 * 1000).toISOString())
        .order('timestamp', { ascending: false })
        .limit(50)
      if (error) {
        console.error('Supabase health query error:', error)
        throw new Error('Failed to fetch health metrics')
      }
      return data || []
    },
    staleTime: 30000,
    refetchInterval: 30000,
    retry: 3,
    onError: (error: unknown) => {
      console.error('Supabase health query failed:', error)
    }
  })

  // Fetch vulnerability data
  const vulnerabilitiesQuery = useQuery({
    queryKey: ['trivy-vulnerabilities'],
    queryFn: async () => {
      const { data, error } = await axios.get('/api/vulnerabilities/summary')
      if (error) {
        console.error('Vulnerabilities API error:', error)
        throw new Error('Failed to fetch vulnerability data')
      }
      return data
    },
    staleTime: 5 * 60 * 1000,
    retry: 1,
    onError: (error: AxiosError | unknown) => {
      console.error('Vulnerabilities query failed:', error)
    }
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
    const container = dockerContainers.find((c: DockerContainer) =>
      c.Names.some((name: string) => name.includes(containerName))
    )
    if (!container) {
      return {
        name: containerName,
        status: 'down' as const,
        lastUpdated: new Date(),
        ariaLabel: `${containerName} service is down`
      }
    }

    const status = container.State.Running ? 'up' : 'down' as ServiceStatus['status']
    return {
      name: containerName,
      status,
      lastUpdated: new Date(container.State.StartedAt),
      ariaLabel: `${containerName} service is ${status === 'up' ? 'running' : 'stopped'}`
    }
  }

  const coreServices: CoreService[] = [
    { name: 'n8n', display: 'n8n Workflow', priority: 1 },
    { name: 'ollama', display: 'Ollama AI', priority: 2 },
    { name: 'flowise', display: 'Flowise', priority: 3 },
    { name: 'qdrant', display: 'Qdrant Vector DB', priority: 4 },
    { name: 'neo4j', display: 'Neo4j Graph DB', priority: 5 },
    { name: 'caddy', display: 'Caddy Proxy', priority: 6 },
    { name: 'langfuse', display: 'Langfuse', priority: 7 },
    { name: 'clickhouse', display: 'ClickHouse', priority: 8 },
    { name: 'minio', display: 'MinIO Storage', priority: 9 },
    { name: 'postgres', display: 'PostgreSQL', priority: 10 },
    { name: 'searxng', display: 'SearxNG Search', priority: 11 }
  ]

  const serviceStatuses = coreServices.map(service =>
    getServiceStatus(service.name)
  ).sort((a, b) => {
    // Prioritize based on service importance and status
    const priorityA = coreServices.find(s => s.name === a.name)?.priority || 99
    const priorityB = coreServices.find(s => s.name === b.name)?.priority || 99
    const statusWeightA = a.status === 'up' ? 0 : 1
    const statusWeightB = b.status === 'up' ? 0 : 1
    
    if (statusWeightA !== statusWeightB) return statusWeightA - statusWeightB
    return priorityA - priorityB
  })

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
    } as const

    const config = statusConfig[status]
    const Icon = config.icon

    return (
      <span
        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${config.className}`}
        role="status"
        aria-label={`Service status: ${status}`}
      >
        <Icon className="w-3 h-3 mr-1" aria-hidden="true" />
        <span>{status.charAt(0).toUpperCase() + status.slice(1)}</span>
      </span>
    )
  }

  if (dockerQuery.isLoading || supabaseQuery.isLoading || vulnerabilitiesQuery.isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-64"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-6xl">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (dockerQuery.isError || supabaseQuery.isError || vulnerabilitiesQuery.isError) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto" />
          <h2 className="text-xl font-semibold text-gray-900">Failed to load dashboard</h2>
          <p className="text-muted-foreground max-w-md">
            There was an error loading the system data. Please refresh the page or try again later.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
          >
            Refresh Page
          </button>
        </div>
      </div>
    )
  }

  return (
    <main className="space-y-6" role="main" aria-label="System Dashboard">
      <header className="flex flex-col lg:flex-row gap-6">
        {/* Main Stats */}
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 flex-1" aria-labelledby="stats-heading">
          <h2 id="stats-heading" className="sr-only">System Statistics</h2>
          
          <Card className="card" role="article" aria-labelledby="uptime-title">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle id="uptime-title" className="text-sm font-medium">System Uptime</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-primary" aria-label={`Uptime: ${uptimePercentage}%`}>
                {uptimePercentage}%
              </div>
              <p className="text-xs text-muted-foreground" aria-describedby="uptime-desc">
                {upServices} of {totalServices} services running
              </p>
              <p id="uptime-desc" className="sr-only">
                {upServices} services are currently operational out of {totalServices} total services
              </p>
            </CardContent>
          </Card>

          <Card className="card" role="article" aria-labelledby="vulns-title">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle id="vulns-title" className="text-sm font-medium">Critical Vulnerabilities</CardTitle>
              <AlertCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${criticalVulnerabilities > 0 ? 'text-red-600' : 'text-green-600'}`}
                   aria-label={`Critical vulnerabilities: ${criticalVulnerabilities}`}>
                {criticalVulnerabilities}
              </div>
              <p className="text-xs text-muted-foreground">
                {totalVulnerabilities} total vulnerabilities
              </p>
            </CardContent>
          </Card>

          <Card className="card" role="article" aria-labelledby="users-title">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle id="users-title" className="text-sm font-medium">Active Users</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold" aria-label="Active users: 12">
                12
              </div>
              <p className="text-xs text-muted-foreground">
                +2 from last week
              </p>
            </CardContent>
          </Card>
        </section>

        {/* Quick Actions */}
        <aside className="lg:w-80" aria-labelledby="actions-heading">
          <h2 id="actions-heading" className="sr-only">Quick Actions</h2>
          <Card className="card">
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Button
                className="w-full flex items-center justify-center space-x-2"
                variant="default"
                aria-label="Update all container images"
                onClick={() => {/* Handle update */}}
              >
                <RefreshCw className="h-4 w-4" />
                <span>Update Images</span>
              </Button>
              <Button
                className="w-full flex items-center justify-center space-x-2"
                variant="default"
                aria-label="Restart all services"
                onClick={() => {/* Handle restart */}}
              >
                <Play className="h-4 w-4" />
                <span>Restart All</span>
              </Button>
              <Button
                className="w-full flex items-center justify-center space-x-2"
                variant="default"
                aria-label="Generate system health report"
                onClick={() => {/* Handle report */}}
              >
                <BarChart3 className="h-4 w-4" />
                <span>Generate Report</span>
              </Button>
            </CardContent>
          </Card>
        </aside>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6" aria-labelledby="services-activity-heading">
        <h2 id="services-activity-heading" className="sr-only">Services and Activity</h2>
        
        {/* Service Status Grid */}
        <article className="card" role="region" aria-labelledby="services-title">
          <CardHeader>
            <CardTitle id="services-title" className="flex items-center space-x-2">
              <Server className="h-5 w-5" />
              <span>Service Status</span>
              <span className="text-xs text-muted-foreground ml-auto">
                {upServices}/{totalServices} running
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div
              className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-96 overflow-y-auto"
              role="list"
              aria-label="Service status list"
            >
              {serviceStatuses.map((service, index) => (
                <div
                  key={index}
                  className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 transition-colors"
                  role="listitem"
                  aria-label={service.ariaLabel}
                >
                  <div
                    className={`w-3 h-3 rounded-full flex-shrink-0 transition-colors ${
                      service.status === 'up' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate" title={service.name}>
                      {coreServices.find(s => s.name === service.name)?.display || service.name}
                    </p>
                    <p
                      className={`text-xs font-medium ${
                        service.status === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}
                      aria-label={`Status: ${service.status}`}
                    >
                      {service.status === 'up' ? 'Running' : 'Stopped'}
                    </p>
                    <time
                      dateTime={service.lastUpdated.toISOString()}
                      className="text-xs text-gray-500 block"
                      aria-label={`Last updated ${service.lastUpdated.toLocaleString()}`}
                    >
                      {service.lastUpdated.toLocaleString('en-US', {
                        hour: '2-digit',
                        minute: '2-digit',
                        hour12: true
                      })}
                    </time>
                  </div>
                  <StatusBadge status={service.status} />
                </div>
              ))}
            </div>
            {serviceStatuses.length === 0 && (
              <div className="text-center py-8 text-muted-foreground" role="alert">
                <Server className="h-12 w-12 mx-auto mb-2 opacity-50" />
                <p>No services configured</p>
              </div>
            )}
          </CardContent>
        </article>

        {/* Recent Activity */}
        <article className="card" role="region" aria-labelledby="activity-title">
          <CardHeader>
            <CardTitle id="activity-title" className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Recent Activity</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="space-y-3" role="list" aria-label="Recent activity log">
              {[
                { time: '2 min ago', event: 'n8n workflow executed successfully', status: 'success' as const },
                { time: '5 min ago', event: 'Ollama model updated', status: 'success' as const },
                { time: '12 min ago', event: 'Trivy scan completed - 3 critical vulnerabilities', status: 'warning' as const },
                { time: '23 min ago', event: 'CI/CD pipeline passed', status: 'success' as const },
                { time: '1 hr ago', event: 'Supabase backup completed', status: 'success' as const },
              ].map((activity, index) => (
                <li
                  key={index}
                  className="flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  role="listitem"
                >
                  <div
                    className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                      activity.status === 'success' ? 'bg-green-500' : 'bg-yellow-500'
                    }`}
                    aria-hidden="true"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-gray-900 leading-tight">{activity.event}</p>
                    <p className="text-xs text-gray-500 mt-1" aria-label={`Time: ${activity.time}`}>
                      {activity.time}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </CardContent>
        </article>
      </section>

      {/* Performance Overview */}
      <section className="card" role="region" aria-labelledby="performance-title">
        <CardHeader>
          <CardTitle id="performance-title" className="flex items-center space-x-2">
            <BarChart3 className="h-5 w-5" />
            <span>Performance Overview</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Real-time system resource utilization and performance metrics
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            {/* CPU Usage */}
            <div className="space-y-4" aria-labelledby="cpu-title">
              <h3 id="cpu-title" className="text-sm font-medium text-gray-900">CPU Usage (Last 24h)</h3>
              <div
                className="h-40 lg:h-48 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg p-4"
                role="img"
                aria-label="CPU usage trend chart showing peaks at 25%, 45%, 30%, 60%, 40%, and 55% over 24 hours"
              >
                <div className="flex items-end h-full space-x-1 sm:space-x-2 relative">
                  {[25, 45, 30, 60, 40, 55].map((usage, index) => (
                    <div
                      key={index}
                      className="flex-1 bg-gradient-to-t from-primary-500 to-primary-600 rounded-sm shadow-sm relative group"
                      style={{ height: `${usage}%` }}
                      aria-hidden="true"
                      title={`${usage}% at ${['1h', '3h', '6h', '12h', '18h', '24h'][index]}`}
                    >
                      <div className="absolute inset-0 bg-white/20 rounded-sm opacity-0 group-hover:opacity-100 transition-opacity" />
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-6 gap-1 mt-3 px-1">
                  {['1h', '3h', '6h', '12h', '18h', '24h'].map((label, index) => (
                    <div
                      key={index}
                      className="text-xs text-center text-gray-500 leading-tight"
                      aria-label={`${label} interval`}
                    >
                      {label}
                    </div>
                  ))}
                </div>
                <div className="mt-2 flex justify-between text-xs text-gray-500">
                  <span>0%</span>
                  <span className="text-primary-600 font-medium">Avg: 42.5%</span>
                  <span>100%</span>
                </div>
              </div>
            </div>

            {/* Memory Usage */}
            <div className="space-y-4" aria-labelledby="memory-title">
              <h3 id="memory-title" className="text-sm font-medium text-gray-900">Memory Usage</h3>
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {[
                  { name: 'Ollama', used: '2.3GB', total: '8GB', percentage: 29, color: 'from-blue-500' },
                  { name: 'Postgres', used: '1.2GB', total: '4GB', percentage: 30, color: 'from-green-500' },
                  { name: 'n8n', used: '450MB', total: '1GB', percentage: 45, color: 'from-orange-500' },
                  { name: 'Qdrant', used: '800MB', total: '2GB', percentage: 40, color: 'from-purple-500' },
                ].map((memory, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-white rounded-lg shadow-sm border" role="listitem">
                    <div className="flex items-center space-x-3 flex-1 min-w-0">
                      <div className={`w-2 h-2 rounded-full ${memory.color} to-${memory.color.replace('from-', 'to-')}`} aria-hidden="true" />
                      <span className="text-sm font-medium text-gray-900 truncate" title={memory.name}>
                        {memory.name}
                      </span>
                    </div>
                    <div className="flex items-center space-x-3 w-48 justify-end">
                      <div className="w-20 bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-2 rounded-full bg-gradient-to-r ${memory.color} to-primary-600 transition-all duration-300`}
                          style={{ width: `${memory.percentage}%` }}
                          aria-hidden="true"
                        />
                      </div>
                      <span
                        className="text-sm font-semibold text-gray-900 min-w-[3ch] text-right"
                        aria-label={`${memory.percentage}% memory usage`}
                      >
                        {memory.percentage}%
                      </span>
                      <span
                        className="text-xs text-gray-500"
                        aria-label={`${memory.used} of ${memory.total} used`}
                      >
                        {memory.used}/{memory.total}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
              <div className="pt-2 border-t text-xs text-gray-500 text-center">
                Total system memory: 15GB used of 32GB (47%)
              </div>
            </div>
          </div>
        </CardContent>
      </section>

      {/* AI Agent Status Section - New addition for AI tools */}
      <section className="card" role="region" aria-labelledby="ai-tools-title">
        <CardHeader>
          <CardTitle id="ai-tools-title" className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>AI Agent Tools</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Status and controls for AI workflow automation and agent capabilities
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              {
                name: 'AI Agent Orchestrator',
                status: 'up' as const,
                description: 'Coordinates multiple AI agents',
                icon: Activity,
                actions: ['View Workflows', 'Configure Agents']
              },
              {
                name: 'Memory Management',
                status: 'warning' as const,
                description: 'Vector database for agent context',
                icon: Database,
                actions: ['Query Memories', 'Manage Storage']
              },
              {
                name: 'Semantic Search',
                status: 'up' as const,
                description: 'AI-powered document search',
                icon: Search,
                actions: ['Search Documents', 'Index New Data']
              } as const,
            ].map((tool, index) => (
              <Card key={index} className="card h-full" role="article">
                <CardHeader className="pb-3">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      tool.status === 'up' ? 'bg-green-500' : 'bg-yellow-500'
                    }`} aria-hidden="true" />
                    <tool.icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
                    <div>
                      <h4 className="font-medium text-gray-900 text-sm">{tool.name}</h4>
                      <p className="text-xs text-muted-foreground">{tool.description}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 space-y-2">
                  <StatusBadge status={tool.status} />
                  <div className="space-y-1">
                    {tool.actions.map((action, aIndex) => (
                      <Button
                        key={aIndex}
                        variant="ghost"
                        size="sm"
                        className="w-full justify-start text-xs h-8"
                        onClick={() => {/* Handle action */}}
                      >
                        {action}
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </section>
    </main>
  )
}
