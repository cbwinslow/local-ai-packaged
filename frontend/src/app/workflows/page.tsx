'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/hooks/useAuth'

export interface Workflow {
  id: string
  name: string
  description: string
  created_at: string
  updated_at: string
  is_active: boolean
}

export default function WorkflowsPage() {
  const { session, loading } = useAuth()
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [triggerLoading, setTriggerLoading] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('')
  const router = useRouter()

  React.useEffect(() => {
    if (!session) return

    // Placeholder workflows (in production, fetch from n8n API)
    const placeholderWorkflows: Workflow[] = [
      { 
        id: 'ingest-bill', 
        name: 'Ingest Bill Data', 
        description: 'Trigger ingestion of new legislative bills from Congress API',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      },
      { 
        id: 'build-graph', 
        name: 'Build Knowledge Graph', 
        description: 'Extract entities and build Neo4j graph from documents',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      },
      { 
        id: 'rag-query', 
        name: 'Run RAG Query', 
        description: 'Execute RAG query on ingested data',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        is_active: true
      }
    ]

    setWorkflows(placeholderWorkflows)
  }, [session])

  const handleTrigger = async (workflowId: string, params: any = {}) => {
    setTriggerLoading(workflowId)
    setStatus('')
    
    try {
      const response = await fetch('/api/workflows/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ workflowId })
      })
      
      if (!response.ok) {
        throw new Error(`Failed to trigger workflow: ${response.statusText}`)
      }
      
      const result = await response.json()
      setStatus(`Workflow triggered successfully: ${result.workflowId}`)
    } catch (error) {
      console.error('Error triggering workflow:', error)
      setStatus(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
    } finally {
      setTriggerLoading(null)
    }
  }

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!session) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-3xl font-bold mb-8">Automated Workflows</h1>
      <div className="max-w-4xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {workflows.map((workflow) => (
            <div key={workflow.id} className="bg-gray-800 p-6 rounded-lg border border-gray-700">
              <h2 className="text-xl font-semibold mb-2">{workflow.name}</h2>
              <p className="text-gray-300 mb-4">{workflow.description}</p>
              <button
                onClick={() => handleTrigger(workflow.id)}
                disabled={triggerLoading === workflow.id}
                className="w-full px-4 py-2 bg-blue-600 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {triggerLoading === workflow.id ? 'Triggering...' : 'Trigger Workflow'}
              </button>
            </div>
          ))}
        </div>
        {status && (
          <div className="mt-8 p-4 bg-green-900 rounded-lg border border-green-700">
            <p>{status}</p>
          </div>
        )}
      </div>
    </div>
  )
}