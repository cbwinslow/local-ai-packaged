import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { CheckCircle, AlertCircle, AlertTriangle, Server, Activity, Database, BarChart3, Play, StopCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/Card'
import { ServiceStatus } from '../types'
import { cn } from '../lib/utils'
import { useState } from 'react'

interface ServiceStatusCardProps {
  serviceName: string
  dockerName: string
  icon: React.ComponentType<{ className?: string }>
  color: string
}

export function ServiceStatusCard({ 
  serviceName, 
  dockerName, 
  icon: Icon, 
  color 
}: ServiceStatusCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const { data: status, isLoading, error } = useQuery<ServiceStatus>({
    queryKey: ['service-status', dockerName],
    queryFn: async () => {
      const response = await axios.get('/api/docker/containers')
      const container = response.data.find((c: any) => 
        c.Names.some((name: string) => name.includes(dockerName))
      )
      
      if (!container) {
        return {
          name: serviceName,
          status: 'down',
          lastUpdated: new Date(),
        }
      }

      return {
        name: serviceName,
        status: container.State.Running ? 'up' : 'down',
        cpu: container.cpu || 0,
        memory: container.memory || 0,
        lastUpdated: new Date(container.State.StartedAt),
      }
    },
    refetchInterval: 10000, // 10 seconds
    staleTime: 5000,
  })

  const getStatusColor = (status?: ServiceStatus['status']) => {
    switch (status) {
      case 'up': return 'text-green-600 bg-green-50 border-green-200'
      case 'down': return 'text-red-600 bg-red-50 border-red-200'
      case 'warning': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      default: return 'text-gray-400 bg-gray-50 border-gray-200'
    }
  }

  const getStatusIcon = (status?: ServiceStatus['status']) => {
    switch (status) {
      case 'up': return CheckCircle
      case 'down': return AlertCircle
      case 'warning': return AlertTriangle
      default: return AlertCircle
    }
  }

  const StatusIcon = status ? getStatusIcon(status.status) : AlertCircle

  const handleRestart = async () => {
    try {
      await axios.post(`/api/docker/containers/${dockerName}/restart`)
      // Invalidate queries to refresh status
      queryClient.invalidateQueries({ queryKey: ['service-status', dockerName] })
    } catch (error) {
      console.error('Restart failed:', error)
    }
  }

  if (isLoading) {
    return (
      <Card className="card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Icon className="h-4 w-4 text-muted-foreground" />
            <span>{serviceName}</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-2">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-3 bg-gray-200 rounded w-1/2"></div>
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
            <Icon className="h-4 w-4" />
            <span>{serviceName}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="text-red-600">
          <p className="text-sm">Error loading status</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="card hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center space-x-2">
            <Icon className={`h-5 w-5 ${color}`} />
            <span>{serviceName}</span>
          </CardTitle>
          <div className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(status?.status)}`}>
            <StatusIcon className="w-3 h-3 inline mr-1" />
            {status?.status || 'unknown'}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className={cn("space-y-3 transition-all", {
        'pt-0': !isExpanded,
        'pt-4': isExpanded
      })}>
        {status && (
          <div className="space-y-2">
            {status.cpu !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">CPU</span>
                <span className="font-medium">{status.cpu}%</span>
              </div>
            )}
            
            {status.memory !== undefined && (
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Memory</span>
                <span className="font-medium">{status.memory}MB</span>
              </div>
            )}
            
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uptime</span>
              <span className="font-medium">
                {status.lastUpdated ? 
                  `${Math.round((Date.now() - new Date(status.lastUpdated).getTime()) / 1000 / 60)}m` : 
                  'N/A'
                }
              </span>
            </div>

            {isExpanded && (
              <div className="pt-4 border-t">
                <div className="flex space-x-2">
                  <button
                    onClick={handleRestart}
                    className="flex-1 flex items-center justify-center space-x-2 px-3 py-2 text-xs font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors"
                    disabled={!status || status.status === 'down'}
                  >
                    {status?.status === 'up' ? (
                      <>
                        <StopCircle className="w-3 h-3" />
                        <span>Restart</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-3 h-3" />
                        <span>Start</span>
                      </>
                    )}
                  </button>
                  
                  <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="px-3 py-2 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    {isExpanded ? 'Less' : 'More'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {!isExpanded && (
          <button
            onClick={() => setIsExpanded(true)}
            className="w-full text-xs text-primary-600 hover:text-primary-700 font-medium py-1"
          >
            View details
          </button>
        )}
      </CardContent>
    </Card>
  )
}