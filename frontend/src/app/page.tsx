'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { 
  CpuChipIcon, 
  CloudIcon, 
  ChartBarIcon, 
  CogIcon,
  PlayIcon,
  DocumentTextIcon,
  ServerIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'

const services = [
  {
    name: 'N8N',
    description: 'Low-code workflow automation',
    icon: CloudIcon,
    url: '/n8n',
    status: 'online'
  },
  {
    name: 'Open WebUI',
    description: 'Chat interface for your LLMs',
    icon: CpuChipIcon,
    url: '/openwebui',
    status: 'online'
  },
  {
    name: 'Flowise',
    description: 'Visual LLM workflow builder',
    icon: ChartBarIcon,
    url: '/flowise',
    status: 'online'
  },
  {
    name: 'Supabase',
    description: 'Database and authentication',
    icon: ServerIcon,
    url: '/supabase',
    status: 'online'
  },
  {
    name: 'Langfuse',
    description: 'LLM observability platform',
    icon: DocumentTextIcon,
    url: '/langfuse',
    status: 'online'
  },
  {
    name: 'Neo4j',
    description: 'Graph database for knowledge graphs',
    icon: ShieldCheckIcon,
    url: '/neo4j',
    status: 'online'
  }
]

export default function HomePage() {
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!mounted) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800">
      {/* Header */}
      <header className="bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <CpuChipIcon className="h-8 w-8 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">Local AI Package</h1>
            </div>
            <nav className="flex space-x-4">
              <Link href="/config" className="text-gray-300 hover:text-white transition-colors">
                Configuration
              </Link>
              <Link href="/auth" className="text-gray-300 hover:text-white transition-colors">
                Authentication
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-5xl font-bold text-white mb-6">
              Self-hosted AI Development Environment
            </h2>
            <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
              A complete stack for local AI development including Ollama, Open WebUI, 
              N8N workflows, Supabase database, and more - all containerized and ready to deploy.
            </p>
            <div className="flex justify-center space-x-4">
              <button className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2">
                <PlayIcon className="h-5 w-5" />
                <span>Get Started</span>
              </button>
              <button className="bg-gray-700 hover:bg-gray-600 text-white px-8 py-3 rounded-lg font-medium transition-colors flex items-center space-x-2">
                <DocumentTextIcon className="h-5 w-5" />
                <span>Documentation</span>
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Services Grid */}
      <section className="py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-white text-center mb-12">
            Available Services
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {services.map((service, index) => (
              <motion.div
                key={service.name}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 hover:bg-gray-800/70 transition-all"
              >
                <div className="flex items-center space-x-3 mb-4">
                  <service.icon className="h-8 w-8 text-blue-400" />
                  <h4 className="text-xl font-semibold text-white">{service.name}</h4>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    service.status === 'online' 
                      ? 'bg-green-900 text-green-300' 
                      : 'bg-red-900 text-red-300'
                  }`}>
                    {service.status}
                  </span>
                </div>
                <p className="text-gray-300 mb-4">{service.description}</p>
                <Link 
                  href={service.url}
                  className="inline-flex items-center text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Access Service
                  <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* System Status */}
      <section className="py-16 bg-gray-800/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h3 className="text-3xl font-bold text-white text-center mb-12">
            System Status
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center">
              <ServerIcon className="h-12 w-12 text-green-400 mx-auto mb-3" />
              <h4 className="text-lg font-semibold text-white mb-2">All Services</h4>
              <p className="text-green-400">Online</p>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center">
              <CpuChipIcon className="h-12 w-12 text-blue-400 mx-auto mb-3" />
              <h4 className="text-lg font-semibold text-white mb-2">CPU Usage</h4>
              <p className="text-gray-300">25%</p>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center">
              <ChartBarIcon className="h-12 w-12 text-yellow-400 mx-auto mb-3" />
              <h4 className="text-lg font-semibold text-white mb-2">Memory</h4>
              <p className="text-gray-300">4.2GB / 16GB</p>
            </div>
            <div className="bg-gray-800/50 backdrop-blur-sm border border-gray-700 rounded-lg p-6 text-center">
              <CloudIcon className="h-12 w-12 text-purple-400 mx-auto mb-3" />
              <h4 className="text-lg font-semibold text-white mb-2">Network</h4>
              <p className="text-gray-300">Active</p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-800/50 border-t border-gray-700 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <p className="text-gray-300">
            Local AI Package - Self-hosted AI Development Environment
          </p>
          <p className="text-gray-500 mt-2">
            Built with Docker, Next.js, and modern AI tools
          </p>
        </div>
      </footer>
    </div>
  )
}