import type { NextApiRequest, NextApiResponse } from 'next'
import Docker from 'dockerode'

const docker = new Docker({
  socketPath: '/var/run/docker.sock',
})

/**
 * HTTP GET handler that returns a list of Docker containers enriched with health status and uptime.
 *
 * Responds with:
 * - 200: JSON array of container objects containing Id, Names, Image, State (Status, Running, StartedAt), Labels, Mounts, plus `healthStatus` ("up" when running) and `uptime` (milliseconds, 0 when not running).
 * - 405: JSON `{ error: 'Method not allowed' }` for non-GET requests.
 * - 500: JSON `{ error: 'Failed to fetch container information', details: string }` on Docker API errors.
 *
 * The returned list includes stopped containers and is limited to 50 entries.
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  // Only allow GET requests
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    // List all containers
    const containers = await docker.listContainers({
      all: true, // Include stopped containers
      limit: 50,
    })

    // Filter and format for dashboard
    const formattedContainers = containers.map(container => ({
      Id: container.Id,
      Names: container.Names,
      Image: container.Image,
      State: {
        Status: container.State,
        Running: container.State === 'running',
        StartedAt: container.Created ? new Date(container.Created * 1000).toISOString() : new Date().toISOString(),
      },
      Labels: container.Labels,
      Mounts: container.Mounts,
    }))

    // Add health status logic
    const containersWithHealth = formattedContainers.map(container => {
      const isHealthy = container.State.Running && container.State.Status === 'running'
      const healthStatus = isHealthy ? 'up' : container.State.Status
      
      return {
        ...container,
        healthStatus,
        uptime: isHealthy ? Date.now() - (container.State.StartedAt ? new Date(container.State.StartedAt).getTime() : 0) : 0,
      }
    })

    res.status(200).json(containersWithHealth)
  } catch (error) {
    console.error('Docker API error:', error)
    res.status(500).json({ 
      error: 'Failed to fetch container information',
      details: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

// Extend NextApiRequest type for authentication
declare module 'next' {
  interface NextApiRequest {
    docker?: Docker
  }
}