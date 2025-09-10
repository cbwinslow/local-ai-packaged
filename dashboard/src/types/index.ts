export interface ServiceStatus {
  name: string
  status: 'up' | 'down' | 'warning'
  cpu?: number
  memory?: number
  lastUpdated: Date
  ariaLabel?: string
}

export interface Vulnerability {
  id: string
  package: string
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  installedVersion: string
  fixedVersion?: string
  title: string
}

export interface TodoItem {
  id: string
  content: string
  status: 'Completed' | 'In Progress' | 'Pending'
}

export interface DockerContainer {
  Id: string
  Names: string[]
  State: {
    Status: string
    Running: boolean
    StartedAt: string
  }
  Image: string
}

export interface HealthMetric {
  service: string
  status: string
  metrics: {
    cpu: number
    memory: number
    uptime: number
  }
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}