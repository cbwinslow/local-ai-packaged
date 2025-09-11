'use client'

import React from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface MetricsData {
  name: string
  value: number
  [key: string]: any
}

interface MetricsChartProps {
  data: MetricsData[]
}

export const MetricsChart: React.FC<MetricsChartProps> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p className="text-gray-400">No metrics data available</p>
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
        <XAxis dataKey="name" stroke="#9CA3AF" />
        <YAxis stroke="#9CA3AF" />
        <Tooltip />
        <Legend />
        <Bar dataKey="value" fill="#3B82F6" />
      </BarChart>
    </ResponsiveContainer>
  )
}