'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import type { Session } from '@supabase/supabase-js'
import { MetricsChart } from '@/components/dashboard/MetricsChart'
import { GraphViewer } from '@/components/dashboard/GraphViewer'

export default function DashboardPage() {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [metrics, setMetrics] = useState<any>(null)
  const router = useRouter()

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setLoading(false)
      if (!session) {
        router.push('/auth')
      }
    })
  }, [router])

  useEffect(() => {
    if (!session) return

    // Subscribe to realtime metrics from Supabase (assume 'metrics' table)
    const subscription = supabase
      .channel('metrics')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'metrics' }, (payload) => {
        setMetrics(payload.new)
      })
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