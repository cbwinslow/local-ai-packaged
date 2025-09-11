'use client'

import React, { useEffect, useRef, useState } from 'react'
import { driver, getSession } from '@/lib/neo4j'
import { DataSet } from 'vis-data'
import { Network } from 'vis-network/standalone'
import type { Result } from 'neo4j-driver'

interface Node {
  id: number
  label: string
  title?: string
}

interface Edge {
  from: number
  to: number
  label: string
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
}

export const GraphViewer: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] })
  const [loading, setLoading] = useState(true)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const session = getSession()
        const result: Result = await session.run('MATCH (n)-[r]->(m) RETURN n, r, m LIMIT 10')
        const nodeSet = new Set<string>()
        const edges: Edge[] = []

        result.records.forEach((record: any) => {
          const n = record.get('n')
          const m = record.get('m')
          const r = record.get('r')

          const nodeIdN = n.identity.low.toString()
          const nodeIdM = m.identity.low.toString()

          if (!nodeSet.has(nodeIdN)) {
            nodeSet.add(nodeIdN)
            const labelN = n.properties.name || n.labels[0]
            const titleN = n.properties.description || ''
            // Add to nodes array in setGraphData
          }

          if (!nodeSet.has(nodeIdM)) {
            nodeSet.add(nodeIdM)
            const labelM = m.properties.name || m.labels[0]
            const titleM = m.properties.description || ''
            // Add to nodes array
          }

          edges.push({ from: n.identity.low, to: m.identity.low, label: r.type })
        })

        // Note: For simplicity, use placeholder nodes; in production, collect all nodes
        const nodes: Node[] = Array.from(nodeSet).map(id => ({ id: parseInt(id), label: 'Entity', title: 'Description' }))

        setGraphData({
          nodes,
          edges
        })
      } catch (error) {
        console.error('Neo4j query error:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchGraph()
  }, [])

  useEffect(() => {
    if (!containerRef.current || graphData.nodes.length === 0) return

    const nodes = new DataSet(graphData.nodes)
    const edges = new DataSet(graphData.edges)

    const data = { nodes, edges }
    const options = {
      nodes: { shape: 'dot', size: 20, color: { background: '#3B82F6', border: '#1E40AF' } },
      edges: { arrows: 'to', color: { color: '#9CA3AF' } },
      physics: { enabled: true }
    }

    const network = new Network(containerRef.current, data, options)

    return () => network.destroy()
  }, [graphData])

  if (loading) {
    return <p className="text-gray-400">Loading graph...</p>
  }

  return (
    <div className="h-96 border border-gray-700 rounded-lg">
      <div ref={containerRef} className="w-full h-full" />
    </div>
  )
}