import { NextRequest, NextResponse } from 'next/server'
import axios from 'axios'

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json()

    // Proxy to RAG API (agentic-knowledge-rag-graph at localhost:8000)
    const response = await axios.post('http://localhost:8000/rag-query', { query }, {
      timeout: 30000 // 30s timeout for RAG processing
    })

    return NextResponse.json({ results: response.data })
  } catch (error) {
    console.error('RAG query error:', error)
    return NextResponse.json({ error: 'Search failed - RAG service unavailable' }, { status: 500 })
  }
}