'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import type { Session } from '@supabase/supabase-js'

export default function SearchPage() {
  const [session, setSession] = useState<Session | null>(null)
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<any>(null)
  const [searchLoading, setSearchLoading] = useState(false)
  const [loading, setLoading] = useState(true)
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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setSearchLoading(true)
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })

      if (response.ok) {
        const data = await response.json()
        setResults(data.results)
      } else {
        setResults({ error: 'Search failed' })
      }
    } catch (error) {
      setResults({ error: 'Network error' })
    } finally {
      setSearchLoading(false)
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
      <h1 className="text-3xl font-bold mb-8">Advanced Search</h1>
      <div className="max-w-4xl mx-auto">
        <form onSubmit={handleSubmit} className="mb-8">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="w-full p-4 rounded-lg bg-gray-800 border border-gray-700 text-white"
            disabled={searchLoading}
          />
          <button
            type="submit"
            disabled={searchLoading || !query.trim()}
            className="mt-4 px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {searchLoading ? 'Searching...' : 'Search'}
          </button>
        </form>
        <div className="mt-8">
          {results ? (
            results.error ? (
              <p className="text-red-400">Error: {results.error}</p>
            ) : (
              <div>
                <h2 className="text-xl font-semibold mb-4">Results:</h2>
                <pre className="bg-gray-800 p-4 rounded-lg text-sm overflow-auto">
                  {JSON.stringify(results, null, 2)}
                </pre>
              </div>
            )
          ) : (
            <p>Search results will appear here...</p>
          )}
        </div>
      </div>
    </div>
  )
}