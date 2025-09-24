'use client'

import { useState } from 'react'
import { useAuth } from '@/hooks/useAuth'

export default function RAGPage() {
  const [query, setQuery] = useState('')
  const [response, setResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const { session, signIn, signOut } = useAuth()

  const handleQuery = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query) return

    setLoading(true)
    try {
      const res = await fetch('http://localhost:8000/rag/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setResponse(data)
    } catch (error) {
      console.error('Query failed:', error)
    }
    setLoading(false)
  }

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <button onClick={signIn} className="px-4 py-2 bg-blue-500 text-white rounded">
          Sign In to Use RAG
        </button>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-8">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-3xl font-bold">RAG Query</h1>
        <button onClick={signOut} className="px-4 py-2 bg-red-500 text-white rounded">
          Sign Out
        </button>
      </div>
      <form onSubmit={handleQuery} className="mb-8">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., Analyze Bill X"
          className="w-full p-4 border rounded mb-4"
        />
        <button type="submit" disabled={loading} className="px-6 py-2 bg-green-500 text-white rounded">
          {loading ? 'Querying...' : 'Submit Query'}
        </button>
      </form>
      {response && (
        <div className="p-4 bg-gray-100 rounded">
          <h2 className="font-bold">Response:</h2>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  )
}