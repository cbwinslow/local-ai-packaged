import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Textarea } from '../components/ui/Textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/Select'
import { Checkbox } from '../components/ui/Checkbox'
import { cn } from '../lib/utils'
import { Save, RefreshCw, Download, Upload, AlertCircle, CheckCircle } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/Tabs'

interface ComposeConfig {
  version: string
  services: Record<string, any>
  volumes: string[]
  networks: Record<string, any>
}

interface EnvironmentVariable {
  key: string
  value: string
  required: boolean
  description?: string
  service?: string
}

const SERVICE_TEMPLATES = {
  n8n: {
    name: 'n8n',
    image: 'n8nio/n8n:1.62.0',
    ports: ['5678:5678'],
    environment: [
      { key: 'N8N_HOST', value: '0.0.0.0', required: true },
      { key: 'N8N_PORT', value: '5678', required: true },
      { key: 'N8N_ENCRYPTION_KEY', value: '', required: true, description: 'Must be 32 characters' },
      { key: 'DB_TYPE', value: 'postgresdb', required: true },
      { key: 'DB_POSTGRESDB_HOST', value: 'postgres', required: true },
    ],
    volumes: ['./n8n_data:/home/node/.n8n'],
  },
  ollama: {
    name: 'ollama',
    image: 'ollama/ollama:0.3.12',
    ports: ['11434:11434'],
    environment: [
      { key: 'OLLAMA_HOST', value: '0.0.0.0', required: true },
      { key: 'OLLAMA_PORT', value: '11434', required: true },
      { key: 'OLLAMA_MAX_LOADED_MODELS', value: '2', required: false },
    ],
    volumes: ['./ollama_data:/root/.ollama'],
    command: 'serve',
  },
  postgres: {
    name: 'postgres',
    image: 'postgres:16-alpine',
    ports: ['5432:5432'],
    environment: [
      { key: 'POSTGRES_USER', value: 'postgres', required: true },
      { key: 'POSTGRES_PASSWORD', value: '', required: true, description: 'Secure password required' },
      { key: 'POSTGRES_DB', value: 'postgres', required: true },
    ],
    volumes: ['./postgres_data:/var/lib/postgresql/data'],
  },
}

export default function ConfigPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('services')
  const [editingService, setEditingService] = useState<string | null>(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [config, setConfig] = useState<ComposeConfig>({
    version: '3.8',
    services: {},
    volumes: [],
    networks: {},
  })

  // Fetch current compose config
  const { data: currentConfig, isLoading: configLoading } = useQuery({
    queryKey: ['compose-config'],
    queryFn: async () => {
      const response = await axios.get('/api/config/compose')
      return response.data
    },
    staleTime: 60000,
  })

  // Fetch environment variables
  const { data: envVars } = useQuery({
    queryKey: ['environment-vars'],
    queryFn: async () => {
      const response = await axios.get('/api/config/env')
      return response.data
    },
  })

  // Save compose config mutation
  const saveConfigMutation = useMutation({
    mutationFn: async (updatedConfig: ComposeConfig) => {
      const response = await axios.post('/api/config/compose', updatedConfig)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['compose-config'] })
      // Trigger docker compose reload
      axios.post('/api/docker/compose/reload')
    },
  })

  // Save environment mutation
  const saveEnvMutation = useMutation({
    mutationFn: async (updatedEnv: EnvironmentVariable[]) => {
      const response = await axios.post('/api/config/env', updatedEnv)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['environment-vars'] })
    },
  })

  const addService = (template: keyof typeof SERVICE_TEMPLATES) => {
    const serviceTemplate = SERVICE_TEMPLATES[template]
    setConfig(prev => ({
      ...prev,
      services: {
        ...prev.services,
        [serviceTemplate.name]: serviceTemplate
      }
    }))
  }

  const updateServiceConfig = (serviceName: string, updates: any) => {
    setConfig(prev => ({
      ...prev,
      services: {
        ...prev.services,
        [serviceName]: {
          ...prev.services[serviceName],
          ...updates
        }
      }
    }))
  }

  const updateEnvVar = (index: number, updates: Partial<EnvironmentVariable>) => {
    if (!envVars) return
    
    const updatedEnv = envVars.map((varItem, i) => 
      i === index ? { ...varItem, ...updates } : varItem
    )
    setConfig(prev => ({ ...prev, environment: updatedEnv }))
  }

  const validateComposeConfig = () => {
    // Basic validation
    const errors: string[] = []
    
    if (!config.version) {
      errors.push('Compose version is required')
    }

    Object.entries(config.services).forEach(([name, service]) => {
      if (!service.image) {
        errors.push(`Service ${name} missing image`)
      }
      
      if (service.ports && !Array.isArray(service.ports)) {
        errors.push(`Service ${name} ports must be an array`)
      }
    })

    return errors
  }

  const handleSave = () => {
    const validationErrors = validateComposeConfig()
    if (validationErrors.length > 0) {
      alert(`Validation errors:\n${validationErrors.join('\n')}`)
      return
    }

    saveConfigMutation.mutate(config)
  }

  const handleSaveEnv = () => {
    if (envVars) {
      saveEnvMutation.mutate(envVars)
    }
  }

  const downloadConfig = () => {
    const configString = JSON.stringify(config, null, 2)
    const blob = new Blob([configString], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'docker-compose.config.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const importedConfig = JSON.parse(e.target?.result as string)
          setConfig(importedConfig)
        } catch (error) {
          alert('Invalid JSON configuration file')
        }
      }
      reader.readAsText(file)
    }
  }

  if (configLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48"></div>
          <div className="h-96 bg-gray-200 rounded-lg"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Configuration</h1>
          <p className="text-muted-foreground mt-2">
            Manage Docker Compose services, environment variables, and deployment settings
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <Button 
            onClick={downloadConfig} 
            variant="outline"
            className="flex items-center space-x-2"
          >
            <Download className="h-4 w-4" />
            <span>Export Config</span>
          </Button>
          <label className="cursor-pointer">
            <input
              type="file"
              accept=".json"
              onChange={handleFileUpload}
              className="hidden"
            />
            <Button variant="outline" asChild>
              <span className="flex items-center space-x-2">
                <Upload className="h-4 w-4" />
                <span>Import Config</span>
              </span>
            </Button>
          </label>
          <Button onClick={handleSave} disabled={saveConfigMutation.isPending}>
            {saveConfigMutation.isPending ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                <span>Saving...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                <span>Save Configuration</span>
              </>
            )}
          </Button>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="services">Services</TabsTrigger>
          <TabsTrigger value="environment">Environment</TabsTrigger>
          <TabsTrigger value="volumes">Volumes & Storage</TabsTrigger>
          <TabsTrigger value="advanced">Advanced</TabsTrigger>
        </TabsList>

        {/* Services Tab */}
        <TabsContent value="services" className="space-y-6">
          <Card className="card">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Docker Compose Services
                <Button 
                  onClick={() => addService('n8n')} 
                  variant="outline"
                  size="sm"
                >
                  Add n8n Service
                </Button>
              </CardTitle>
              <CardDescription>
                Configure your AI platform services with custom settings
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {Object.entries(config.services).map(([serviceName, service]) => (
                  <Card key={serviceName} className="card">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                            <Server className="h-5 w-5 text-primary-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold text-gray-900">{serviceName}</h4>
                            <p className="text-sm text-muted-foreground">
                              {service.image || 'No image specified'}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setEditingService(editingService === serviceName ? null : serviceName)}
                          >
                            {editingService === serviceName ? 'Cancel' : 'Edit'}
                          </Button>
                          <Button variant="destructive" size="sm">
                            Remove
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    
                    <CardContent className={cn("space-y-4 transition-all", {
                      'pt-4 border-t': editingService === serviceName
                    })}>
                      {!editingService && (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          <div>
                            <label className="text-sm font-medium text-gray-900 block mb-1">Status</label>
                            <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                              service.restart === 'unless-stopped' 
                                ? 'bg-green-100 text-green-800' 
                                : 'bg-gray-100 text-gray-800'
                            }`}>
                              {service.restart || 'always'}
                            </div>
                          </div>
                          
                          {service.ports && (
                            <div>
                              <label className="text-sm font-medium text-gray-900 block mb-1">Ports</label>
                              <div className="flex flex-wrap gap-1">
                                {service.ports.map((port: string, index: number) => (
                                  <span key={index} className="px-2 py-1 bg-gray-100 text-xs rounded">
                                    {port}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {service.volumes && (
                            <div>
                              <label className="text-sm font-medium text-gray-900 block mb-1">Volumes</label>
                              <div className="text-xs text-gray-600">
                                {service.volumes?.length || 0} mounted
                              </div>
                            </div>
                          )}
                          
                          <div className="col-span-1 md:col-span-2 lg:col-span-1">
                            <label className="text-sm font-medium text-gray-900 block mb-1">Environment</label>
                            <div className="text-xs text-gray-600">
                              {Object.keys(service.environment || {}).length} variables
                            </div>
                          </div>
                        </div>
                      )}

                      {editingService === serviceName && (
                        <div className="space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <label className="text-sm font-medium text-gray-900 block mb-2">Image</label>
                              <Input
                                value={service.image || ''}
                                onChange={(e) => updateServiceConfig(serviceName, { image: e.target.value })}
                                placeholder="e.g., n8nio/n8n:1.62.0"
                                className="text-sm"
                              />
                            </div>
                            
                            <div>
                              <label className="text-sm font-medium text-gray-900 block mb-2">Restart Policy</label>
                              <Select
                                value={service.restart || 'unless-stopped'}
                                onValueChange={(value) => updateServiceConfig(serviceName, { restart: value })}
                              >
                                <SelectTrigger className="text-sm">
                                  <SelectValue placeholder="Select restart policy" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="no">No</SelectItem>
                                  <SelectItem value="on-failure">On Failure</SelectItem>
                                  <SelectItem value="always">Always</SelectItem>
                                  <SelectItem value="unless-stopped">Unless Stopped</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>
                          
                          <div>
                            <label className="text-sm font-medium text-gray-900 block mb-2">Ports</label>
                            <div className="space-y-2">
                              {(service.ports || []).map((port: string, index: number) => (
                                <div key={index} className="flex space-x-2">
                                  <Input
                                    value={port}
                                    onChange={(e) => {
                                      const newPorts = [...(service.ports || [])]
                                      newPorts[index] = e.target.value
                                      updateServiceConfig(serviceName, { ports: newPorts })
                                    }}
                                    placeholder="e.g., 5678:5678"
                                    className="flex-1 text-sm"
                                  />
                                  <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      const newPorts = (service.ports || []).filter((_: string, i: number) => i !== index)
                                      updateServiceConfig(serviceName, { ports: newPorts })
                                    }}
                                  >
                                    Remove
                                  </Button>
                                </div>
                              ))}
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => updateServiceConfig(serviceName, { 
                                  ports: [...(service.ports || []), ''] 
                                })}
                              >
                                Add Port
                              </Button>
                            </div>
                          </div>

                          <div>
                            <label className="text-sm font-medium text-gray-900 block mb-2">Environment Variables</label>
                            <div className="space-y-2 max-h-48 overflow-y-auto">
                              {(service.environment || []).map((env: EnvironmentVariable, index: number) => (
                                <div key={index} className="flex space-x-2 items-start">
                                  <Input
                                    value={env.key}
                                    onChange={(e) => {
                                      const newEnv = [...(service.environment || [])]
                                      newEnv[index] = { ...newEnv[index], key: e.target.value }
                                      updateServiceConfig(serviceName, { environment: newEnv })
                                    }}
                                    placeholder="KEY"
                                    className="flex-1 text-sm"
                                  />
                                  <Input
                                    type={env.key.toUpperCase().includes('PASSWORD') || env.key.toUpperCase().includes('SECRET') ? 'password' : 'text'}
                                    value={env.value}
                                    onChange={(e) => {
                                      const newEnv = [...(service.environment || [])]
                                      newEnv[index] = { ...newEnv[index], value: e.target.value }
                                      updateServiceConfig(serviceName, { environment: newEnv })
                                    }}
                                    placeholder="value"
                                    className="flex-1 text-sm"
                                  />
                                  <Button
                                    type="button"
                                    variant="outline"
                                    size="sm"
                                    onClick={() => {
                                      const newEnv = (service.environment || []).filter((_: EnvironmentVariable, i: number) => i !== index)
                                      updateServiceConfig(serviceName, { environment: newEnv })
                                    }}
                                  >
                                    Remove
                                  </Button>
                                </div>
                              ))}
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => updateServiceConfig(serviceName, { 
                                  environment: [...(service.environment || []), { key: '', value: '', required: false }] 
                                })}
                              >
                                Add Variable
                              </Button>
                            </div>
                          </div>

                          {showAdvanced && (
                            <div className="space-y-4">
                              <div>
                                <label className="text-sm font-medium text-gray-900 block mb-2">Volumes</label>
                                <Textarea
                                  value={(service.volumes || []).join('\n')}
                                  onChange={(e) => updateServiceConfig(serviceName, { 
                                    volumes: e.target.value.split('\n').filter(v => v.trim()) 
                                  })}
                                  placeholder="e.g., ./data:/app/data"
                                  className="text-sm"
                                  rows={3}
                                />
                              </div>

                              <div>
                                <label className="text-sm font-medium text-gray-900 block mb-2">Command</label>
                                <Input
                                  value={service.command || ''}
                                  onChange={(e) => updateServiceConfig(serviceName, { command: e.target.value })}
                                  placeholder="e.g., serve"
                                  className="text-sm"
                                />
                              </div>

                              <div>
                                <label className="text-sm font-medium text-gray-900 block mb-2">Depends On</label>
                                <Input
                                  value={(service.depends_on || []).join(',')}
                                  onChange={(e) => updateServiceConfig(serviceName, { 
                                    depends_on: e.target.value.split(',').map(s => s.trim()).filter(s => s) 
                                  })}
                                  placeholder="e.g., postgres, redis"
                                  className="text-sm"
                                />
                              </div>
                            </div>
                          )}

                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="w-full"
                          >
                            {showAdvanced ? 'Hide Advanced Settings' : 'Show Advanced Settings'}
                          </Button>

                          <div className="flex space-x-2 pt-4 border-t">
                            <Button 
                              onClick={() => setEditingService(null)}
                              className="flex-1"
                            >
                              Cancel
                            </Button>
                            <Button 
                              onClick={handleSave}
                              className="flex-2"
                            >
                              <Save className="h-4 w-4 mr-2" />
                              Save Service
                            </Button>
                          </div>
                        </div>
                      )}

                      {serviceName === 'n8n' && (
                        <div className="p-4 bg-blue-50 rounded-lg">
                          <div className="flex items-start space-x-3">
                            <AlertCircle className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
                            <div>
                              <h5 className="text-sm font-medium text-blue-900">n8n Configuration Tips</h5>
                              <ul className="text-sm text-blue-800 mt-1 space-y-0.5">
                                <li className="flex items-center">
                                  <CheckCircle className="w-3 h-3 text-green-500 mr-2" />
                                  Use PostgreSQL for production databases
                                </li>
                                <li className="flex items-center">
                                  <CheckCircle className="w-3 h-3 text-green-500 mr-2" />
                                  Set N8N_ENCRYPTION_KEY to 32 characters for security
                                </li>
                                <li className="flex items-center">
                                  <CheckCircle className="w-3 h-3 text-green-500 mr-2" />
                                  Configure WEBHOOK_URL for external integrations
                                </li>
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
                
                {Object.keys(config.services).length === 0 && (
                  <div className="text-center py-12">
                    <Server className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Services Configured</h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      Start by adding services using the templates below
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
                      {Object.entries(SERVICE_TEMPLATES).map(([key, template]) => (
                        <Card key={key} className="card cursor-pointer hover:shadow-md transition-shadow" onClick={() => addService(key as keyof typeof SERVICE_TEMPLATES)}>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-base flex items-center space-x-2">
                              <Server className="h-4 w-4" />
                              <span>{template.name}</span>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="text-sm text-muted-foreground">
                            <p>AI Workflow Automation</p>
                            <p className="text-xs mt-1">{template.image}</p>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Environment Tab */}
          <TabsContent value="environment" className="space-y-6">
            <Card className="card">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Environment Variables
                  <div className="flex space-x-2">
                    <Button 
                      onClick={handleSaveEnv}
                      variant="outline"
                      size="sm"
                      disabled={saveEnvMutation.isPending}
                    >
                      {saveEnvMutation.isPending ? (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4 mr-2" />
                          <span>Save Env</span>
                        </>
                      )}
                    </Button>
                  </div>
                </CardTitle>
                <CardDescription>
                  Configure environment variables for all services. Required variables are marked with *
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {(envVars || []).map((envVar, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                      <Checkbox
                        id={`env-required-${index}`}
                        checked={envVar.required}
                        onCheckedChange={(checked) => updateEnvVar(index, { required: checked })}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <label htmlFor={`env-required-${index}`} className="text-sm font-medium text-gray-900 block">
                          {envVar.key}
                          {envVar.required && <span className="text-red-600 ml-1">*</span>}
                        </label>
                        {envVar.description && (
                          <p className="text-xs text-gray-500 mt-1">{envVar.description}</p>
                        )}
                      </div>
                      <Input
                        value={envVar.value}
                        onChange={(e) => updateEnvVar(index, { value: e.target.value })}
                        placeholder={envVar.key}
                        className="flex-1 text-sm"
                        type={envVar.key.toUpperCase().includes('PASSWORD') || envVar.key.toUpperCase().includes('SECRET') ? 'password' : 'text'}
                      />
                      {envVar.service && (
                        <span className="text-xs text-gray-500 bg-blue-50 px-2 py-1 rounded">
                          {envVar.service}
                        </span>
                      )}
                    </div>
                  ))}
                  
                  {/* Add new environment variable */}
                  <div className="flex space-x-3 p-3 bg-gray-50 rounded">
                    <Input
                      placeholder="NEW_KEY"
                      className="flex-1 text-sm"
                    />
                    <Input
                      placeholder="value"
                      className="flex-1 text-sm"
                    />
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        if (envVars) {
                          const newEnv = [...envVars, { 
                            key: '', 
                            value: '', 
                            required: false,
                            description: ''
                          }]
                          // Update envVars state or dispatch action
                          console.log('Add new env var:', newEnv)
                        }
                      }}
                    >
                      Add Variable
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Environment Presets */}
            <Card className="card">
              <CardHeader>
                <CardTitle>Environment Presets</CardTitle>
                <CardDescription>
                  Quick setup for common service configurations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="card cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-base">Production Ready</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      <ul className="list-disc list-inside space-y-1">
                        <li>Secure default passwords</li>
                        <li>Production restart policies</li>
                        <li>Health checks enabled</li>
                        <li>Logging configured</li>
                        <li>Resource limits applied</li>
                      </ul>
                      <Button variant="outline" size="sm" className="mt-3 w-full">
                        Apply Production Preset
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="card cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-base">Development</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      <ul className="list-disc list-inside space-y-1">
                        <li>Development ports exposed</li>
                        <li>Hot reload enabled</li>
                        <li>Debug logging</li>
                        <li>Local development URLs</li>
                        <li>Auto-restart on failure</li>
                      </ul>
                      <Button variant="outline" size="sm" className="mt-3 w-full">
                        Apply Dev Preset
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="card cursor-pointer hover:shadow-md transition-shadow">
                    <CardHeader>
                      <CardTitle className="text-base">Minimal</CardTitle>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      <ul className="list-disc list-inside space-y-1">
                        <li>Essential services only</li>
                        <li>Reduced resource usage</li>
                        <li>Core functionality</li>
                        <li>Smaller images</li>
                        <li>Basic security</li>
                      </ul>
                      <Button variant="outline" size="sm" className="mt-3 w-full">
                        Apply Minimal Preset
                      </Button>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Volumes Tab */}
          <TabsContent value="volumes" className="space-y-6">
            <Card className="card">
              <CardHeader>
                <CardTitle>Storage Volumes</CardTitle>
                <CardDescription>
                  Manage persistent data storage for services
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-900 block mb-2">Database Volume</label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Input
                            placeholder="./postgres_data:/var/lib/postgresql/data"
                            className="text-sm"
                          />
                          <p className="text-xs text-muted-foreground mt-1">Local Path</p>
                        </div>
                        <div>
                          <Input
                            placeholder="/var/lib/postgresql/data"
                            className="text-sm"
                          />
                          <p className="text-xs text-muted-foreground mt-1">Container Path</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 mt-3">
                        <Checkbox id="postgres-backup" />
                        <label htmlFor="postgres-backup" className="text-sm text-gray-900">
                          Enable automatic backups
                        </label>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-900 block mb-2">n8n Volume</label>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <Input
                            placeholder="./n8n_data:/home/node/.n8n"
                            className="text-sm"
                          />
                          <p className="text-xs text-muted-foreground mt-1">Local Path</p>
                        </div>
                        <div>
                          <Input
                            placeholder="/home/node/.n8n"
                            className="text-sm"
                          />
                          <p className="text-xs text-muted-foreground mt-1">Container Path</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-4 mt-3">
                        <Checkbox id="n8n-backup" />
                        <label htmlFor="n8n-backup" className="text-sm text-gray-900">
                          Enable automatic backups
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <h4 className="text-sm font-medium text-blue-900 mb-2">Volume Management</h4>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className="text-lg font-bold text-primary-600">12.5 GB</div>
                        <div className="text-xs text-blue-800">Total Storage</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">8.2 GB</div>
                        <div className="text-xs text-blue-800">Used</div>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-orange-600">4.3 GB</div>
                        <div className="text-xs text-blue-800">Available</div>
                      </div>
                    </div>
                    <div className="mt-4 flex space-x-2">
                      <Button className="flex-1" variant="outline">
                        <RefreshCw className="h-4 w-4 mr-2" />
                        <span>Refresh Volumes</span>
                      </Button>
                      <Button className="flex-1" variant="outline">
                        Backup All
                      </Button>
                      <Button className="flex-1" variant="outline">
                        Prune Unused
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Advanced Tab */}
          <TabsContent value="advanced" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card className="card">
                <CardHeader>
                  <CardTitle>Deployment Settings</CardTitle>
                  <CardDescription>
                    Configure deployment behavior and resource limits
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-900 block mb-1">Default Resource Limits</label>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">CPU Limit</label>
                        <Input
                          placeholder="2.0"
                          className="text-sm w-full"
                        />
                        <span className="text-xs text-muted-foreground">cores</span>
                      </div>
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">Memory Limit</label>
                        <Input
                          placeholder="4.0"
                          className="text-sm w-full"
                        />
                        <span className="text-xs text-muted-foreground">GB</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-gray-900 block mb-1">Update Strategy</label>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <Checkbox id="auto-updates" />
                        <label htmlFor="auto-updates" className="text-sm">
                          Automatic image updates
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="rolling-updates" />
                        <label htmlFor="rolling-updates" className="text-sm">
                          Rolling updates (zero-downtime)
                        </label>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Checkbox id="health-checks" />
                        <label htmlFor="health-checks" className="text-sm">
                          Health checks on startup
                        </label>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t space-y-2">
                    <h5 className="text-sm font-medium text-gray-900">Security Settings</h5>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="non-root-user" />
                      <label htmlFor="non-root-user" className="text-sm">
                        Run services as non-root user
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="network-isolation" />
                      <label htmlFor="network-isolation" className="text-sm">
                        Enable network isolation
                      </label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox id="scan-on-deploy" />
                      <label htmlFor="scan-on-deploy" className="text-sm">
                        Scan on deployment
                      </label>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="card">
                <CardHeader>
                  <CardTitle>Monitoring & Alerts</CardTitle>
                  <CardDescription>
                    Configure alerts and monitoring thresholds
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-gray-900 mb-2">CPU Alert Threshold</h5>
                    <div className="flex items-center space-x-4">
                      <Input
                        type="number"
                        placeholder="80"
                        className="w-20 text-sm"
                        min={0}
                        max={100}
                      />
                      <span className="text-sm text-muted-foreground">%</span>
                      <span className="text-xs text-gray-500">Alert when CPU exceeds threshold</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-gray-900 mb-2">Memory Alert Threshold</h5>
                    <div className="flex items-center space-x-4">
                      <Input
                        type="number"
                        placeholder="90"
                        className="w-20 text-sm"
                        min={0}
                        max={100}
                      />
                      <span className="text-sm text-muted-foreground">%</span>
                      <span className="text-xs text-gray-500">Alert when memory usage is high</span>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <h5 className="text-sm font-medium text-gray-900 mb-2">Notification Settings</h5>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                        <Checkbox id="email-alerts" />
                        <div className="space-y-1">
                          <label htmlFor="email-alerts" className="text-sm font-medium">
                            Email Notifications
                          </label>
                          <p className="text-xs text-gray-600">Send alerts to admin@company.com</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                        <Checkbox id="slack-alerts" />
                        <div className="space-y-1">
                          <label htmlFor="slack-alerts" className="text-sm font-medium">
                            Slack Integration
                          </label>
                          <p className="text-xs text-gray-600">Post to #security-alerts channel</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded">
                        <Checkbox id="webhook-alerts" />
                        <div className="space-y-1">
                          <label htmlFor="webhook-alerts" className="text-sm font-medium">
                            Webhook
                          </label>
                          <p className="text-xs text-gray-600">Send to custom webhook URL</p>
                          <Input
                            placeholder="https://hooks.slack.com/..."
                            className="mt-1 w-full text-sm"
                          />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="pt-4 border-t space-y-2">
                    <h5 className="text-sm font-medium text-gray-900">Alert History</h5>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex justify-between py-1 border-b">
                        <span>High CPU Alert - Ollama</span>
                        <span className="text-green-600">Resolved</span>
                      </div>
                      <div className="flex justify-between py-1 border-b">
                        <span>Critical Vulnerability Alert</span>
                        <span className="text-orange-600">Active</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span>Service Down Alert - n8n</span>
                        <span className="text-green-600">Resolved</span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Advanced Tab */}
          <TabsContent value="advanced">
            <Card className="card">
              <CardHeader>
                <CardTitle>Advanced Configuration</CardTitle>
                <CardDescription>
                  Fine-tune networking, security, and performance settings
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h5 className="text-sm font-medium text-gray-900 mb-3">Network Configuration</h5>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <Checkbox id="internal-network" />
                        <label htmlFor="internal-network" className="text-sm">
                          Internal network isolation
                        </label>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <Checkbox id="expose-internal" />
                        <label htmlFor="expose-internal" className="text-sm">
                          Expose internal services
                        </label>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium text-gray-900 block mb-2">Custom Networks</label>
                        <Input
                          placeholder="Add custom network name"
                          className="text-sm"
                        />
                      </div>
                    </div>
                  </div>

                  <div>
                    <h5 className="text-sm font-medium text-gray-900 mb-3">Performance Tuning</h5>
                    <div className="space-y-3">
                      <div className="flex items-center space-x-3">
                        <Checkbox id="cpu-optimization" />
                        <label htmlFor="cpu-optimization" className="text-sm">
                          Enable CPU optimization flags
                        </label>
                      </div>
                      
                      <div className="flex items-center space-x-3">
                        <Checkbox id="memory-optimization" />
                        <label htmlFor="memory-optimization" className="text-sm">
                          Memory optimization (swap disabled)
                        </label>
                      </div>
                      
                      <div>
                        <label className="text-sm font-medium text-gray-900 block mb-2">Max Container Memory</label>
                        <Input
                          type="number"
                          placeholder="2.0"
                          className="text-sm w-20"
                          min={0}
                        />
                        <span className="text-xs text-muted-foreground ml-2">GB (global limit)</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t space-y-4">
                  <h5 className="text-sm font-medium text-gray-900 mb-3">Security & Compliance</h5>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-900 block mb-2">Security Scan Frequency</label>
                      <Select defaultValue="weekly">
                        <SelectTrigger className="text-sm">
                          <SelectValue placeholder="Weekly" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="daily">Daily</SelectItem>
                          <SelectItem value="weekly">Weekly</SelectItem>
                          <SelectItem value="biweekly">Bi-weekly</SelectItem>
                          <SelectItem value="monthly">Monthly</SelectItem>
                          <SelectItem value="manual">Manual</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-900 block mb-2">Compliance Reports</label>
                      <Select defaultValue="monthly">
                        <SelectTrigger className="text-sm">
                          <SelectValue placeholder="Monthly" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="weekly">Weekly</SelectItem>
                          <SelectItem value="monthly">Monthly</SelectItem>
                          <SelectItem value="quarterly">Quarterly</SelectItem>
                          <SelectItem value="annual">Annual</SelectItem>
                          <SelectItem value="none">None</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h6 className="text-xs font-medium text-gray-900 uppercase tracking-wide mb-2">
                      Audit Trail
                    </h6>
                    <div className="text-xs text-gray-500 space-y-1">
                      <div className="flex justify-between py-1">
                        <span>Config saved by admin</span>
                        <span className="text-green-600">2 min ago</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span>n8n service added</span>
                        <span className="text-green-600">5 min ago</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span>Environment updated</span>
                        <span className="text-green-600">12 min ago</span>
                      </div>
                      <div className="flex justify-between py-1">
                        <span>Security scan triggered</span>
                        <span className="text-blue-600">1 hr ago</span>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Validation Errors */}
        {saveConfigMutation.error && (
          <Card className="card border-red-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center space-x-2 text-red-600">
                <AlertCircle className="h-4 w-4" />
                <span>Configuration Errors</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-red-600 text-sm">
              <ul className="list-disc list-inside space-y-1">
                {saveConfigMutation.error.response?.data?.errors?.map((error: string, index: number) => (
                  <li key={index}>{error}</li>
                )) || [saveConfigMutation.error.message || 'Unknown configuration error']}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Save Status */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <Button variant="outline" onClick={() => {
            setConfig(currentConfig || { version: '3.8', services: {}, volumes: [], networks: {} })
          }}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset to Default
          </Button>
          <Button onClick={handleSave} disabled={saveConfigMutation.isPending || !currentConfig}>
            <Save className="h-4 w-4 mr-2" />
            Save All Changes
          </Button>
        </div>
      </div>
    </div>
  )
}

// Temporary UI components for config page
const Button = ({ children, className, variant = 'default', size = 'default', ...props }: any) => (
  <button className={cn(
    'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none',
    'h-10 py-2 px-4',
    'bg-primary text-primary-foreground hover:bg-primary/90',
    'text-sm',
    variant === 'outline' && 'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
    size === 'sm' && 'h-9 px-3 rounded-md',
    className
  )} {...props}>
    {children}
  </button>
)

const Input = ({ className, ...props }: any) => (
  <input className={cn(
    'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )} {...props} 
  />
)

const Textarea = ({ className, ...props }: any) => (
  <textarea className={cn(
    'flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )} {...props} 
  />
)

const Select = ({ children, ...props }: any) => (
  <div className="relative" {...props}>
    {children}
  </div>
)

const SelectTrigger = ({ className, children, ...props }: any) => (
  <div className={cn(
    'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
    className
  )} {...props}>
    {children}
  </div>
)

const SelectValue = ({ placeholder, ...props }: any) => (
  <span className="text-muted-foreground">{props.children || placeholder}</span>
)

const SelectContent = ({ children, ...props }: any) => (
  <div className="absolute z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-left-2 data-[side=right]:slide-in-from-right-2 data-[side=top]:slide-in-from-bottom-2" {...props}>
    {children}
  </div>
)

const SelectItem = ({ children, ...props }: any) => (
  <div className="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none focus:bg-accent data-[disabled]:pointer-events-none data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground data-[disabled]:opacity-50" {...props}>
    {children}
  </div>
)

const Checkbox = ({ className, ...props }: any) => (
  <input 
    type="checkbox"
    className={cn(
      'h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary',
      className
    )} 
    {...props} 
  />
)

const Tabs = ({ value, onValueChange, className, ...props }: any) => (
  <div role="tablist" className={cn("inline-block", className)} {...props}>
    {props.children}
  </div>
)

const TabsList = ({ className, ...props }: any) => (
  <div className={cn(
    "inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground",
    className
  )} {...props} 
  />
)

const TabsTrigger = ({ value: triggerValue, onClick, children, ...props }: any) => (
  <button
    type="button"
    onClick={(e) => {
      onClick(triggerValue)
      props.onClick?.(e)
    }}
    className={cn(
      "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm",
      props.className
    )}
    {...props}
  >
    {children}
  </button>
)

const TabsContent = ({ value: contentValue, className, ...props }: any) => (
  <div className={cn(
    "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
    contentValue !== props.value && "hidden",
    className
  )} {...props} />
)