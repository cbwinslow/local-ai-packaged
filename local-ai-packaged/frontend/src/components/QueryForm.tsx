'use client'

import { useState } from 'react'

interface QueryResponse {
  response: string
  sources?: string[]
}

export default function QueryForm() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState<QueryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await fetch('http://localhost:8000/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`)
      }

      const data: QueryResponse = await res.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-2xl space-y-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="query" className="block text-sm font-medium text-gray-700">
            Enter your query:
          </label>
          <input
            id="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
            placeholder="Ask about your knowledge graph..."
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="disabled:opacity-50 disabled:cursor-not-allowed w-full justify-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2"
        >
          {loading ? 'Querying...' : 'Submit Query'}
        </button>
      </form>

      {error && (
        <div className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-md">
          Error: {error}
        </div>
      )}

      {result && (
        <div className="mt-4 space-y-4">
          <div className="p-4 bg-blue-100 border border-blue-400 rounded-md">
            <h3 className="font-semibold text-blue-800">Response:</h3>
            <p className="mt-2">{result.response}</p>
          </div>
          {result.sources && result.sources.length > 0 && (
            <div className="p-4 bg-green-100 border border-green-400 rounded-md">
              <h3 className="font-semibold text-green-800">Sources:</h3>
              <ul className="mt-2 list-disc list-inside space-y-1">
                {result.sources.map((source, index) => (
                  <li key={index} className="text-green-700">{source}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}