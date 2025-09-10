import type { NextApiRequest, NextApiResponse } from 'next'
import fs from 'fs'
import path from 'path'

interface VulnerabilitySummary {
  total: number
  critical: number
  high: number
  medium: number
  low: number
  fixedAvailable: number
  servicesAffected: string[]
}

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<VulnerabilitySummary>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const trivyReportPath = path.join(process.cwd(), 'reports', 'trivy-scan.md')
    
    if (!fs.existsSync(trivyReportPath)) {
      return res.status(404).json({
        total: 0,
        critical: 0,
        high: 0,
        medium: 0,
        low: 0,
        fixedAvailable: 0,
        servicesAffected: []
      })
    }

    const reportContent = fs.readFileSync(trivyReportPath, 'utf8')
    
    // Parse Trivy report (assuming table format)
    const lines = reportContent.split('\n')
    let total = 0
    let critical = 0
    let high = 0
    let medium = 0
    let low = 0
    let fixedAvailable = 0
    const servicesAffected = new Set<string>()

    lines.forEach(line => {
      // Look for vulnerability lines in Trivy table format
      if (line.includes('HIGH') || line.includes('CRITICAL') || line.includes('MEDIUM') || line.includes('LOW')) {
        total++
        
        if (line.includes('CRITICAL')) {
          critical++
        } else if (line.includes('HIGH')) {
          high++
        } else if (line.includes('MEDIUM')) {
          medium++
        } else if (line.includes('LOW')) {
          low++
        }

        // Extract service/image name from line
        const imageMatch = line.match(/([a-zA-Z0-9/-]+):[a-zA-Z0-9.-]+/)
        if (imageMatch) {
          servicesAffected.add(imageMatch[1])
        }

        // Check if fixed version is available
        if (line.includes('->') || line.includes('fixed')) {
          fixedAvailable++
        }
      }
    })

    const summary: VulnerabilitySummary = {
      total,
      critical,
      high,
      medium,
      low,
      fixedAvailable,
      servicesAffected: Array.from(servicesAffected)
    }

    res.status(200).json(summary)
  } catch (error) {
    console.error('Vulnerability scan parsing error:', error)
    res.status(500).json({
      total: 0,
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
      fixedAvailable: 0,
      servicesAffected: [],
      error: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}