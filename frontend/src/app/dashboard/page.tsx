'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { MetricsChart } from '@/components/dashboard/MetricsChart'
import { GraphViewer } from '@/components/dashboard/GraphViewer'
import { useAuth } from '@/hooks/useAuth'
import { supabase } from '@/lib/supabase'

interface MetricsPayload {
  new: {
    id: string
    name: string
    value: number
    created_at: string
  }
}

export default function DashboardPage() {
  const { session, loading } = useAuth()
  const [metrics, setMetrics] = useState<{ name: string; value: number }[]>([])
  const router = useRouter()

  useEffect(() => {
    if (!session) return

    // Subscribe to realtime metrics from Supabase
    const subscription = supabase
      .channel('metrics')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'metrics',
        },
        (payload) => {
          const newMetric = {
            name: payload.new.name,
            value: payload.new.value,
            createdAt: new Date(payload.new.created_at).toLocaleTimeString()
          }
          setMetrics(prev => [...prev, newMetric].slice(-10)) // Keep only last 10 metrics
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(subscription)
    }
  }, [session])

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>
  }

  if (!session) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-4">
      <h1 className="text-3xl font-bold mb-8">Data Dashboard</h1>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 max-w-6xl mx-auto">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">System Metrics</h2>
          {metrics ? (
            <MetricsChart data={metrics} />
          ) : (
            <p>Loading metrics...</p>
          )}
        </div>
        <div className="bg-gray-800 p-6 rounded-lg">
          <h2 className="text-xl font-semibold mb-4">Knowledge Graph</h2>
          <GraphViewer />
        </div>
      </div>
    </div>
  )
}