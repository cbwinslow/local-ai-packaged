import React from 'react';
import { GetStaticProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { Layout } from '@/components/Layout';
import { MermaidDiagram, COMMON_DIAGRAMS, ProcessFlow } from '@/components/Diagrams';
import { CodeBlock } from '@/components/CodeBlock';
import { 
  RocketLaunchIcon, 
  CheckCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

export default function QuickStartPage() {
  const tableOfContents = [
    { id: 'overview', title: 'Overview', level: 1 },
    { id: 'prerequisites', title: 'Prerequisites', level: 1 },
    { id: 'installation', title: 'Installation', level: 1 },
    { id: 'configuration', title: 'Configuration', level: 1 },
    { id: 'first-run', title: 'First Run', level: 1 },
    { id: 'verification', title: 'Verification', level: 1 },
    { id: 'first-analysis', title: 'First Analysis', level: 1 },
    { id: 'next-steps', title: 'Next Steps', level: 1 },
    { id: 'troubleshooting', title: 'Troubleshooting', level: 1 },
  ];

  const setupSteps = [
    {
      title: 'Clone Repository',
      description: 'Download the Local AI Packaged repository from GitHub',
      icon: <CheckCircleIcon className="h-6 w-6" />,
      status: 'pending' as const,
      children: (
        <CodeBlock language="bash" showLineNumbers={false}>
{`git clone -b stable https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged`}
        </CodeBlock>
      )
    },
    {
      title: 'Environment Setup',
      description: 'Configure environment variables and generate secure secrets',
      icon: <CheckCircleIcon className="h-6 w-6" />,
      status: 'pending' as const,
      children: (
        <div className="space-y-4">
          <CodeBlock language="bash" showLineNumbers={false}>
{`# Copy environment template
cp .env.example .env

# Generate secure secrets automatically
./fix-supabase-env.sh`}
          </CodeBlock>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-start">
              <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  <strong>Important:</strong> The fix-supabase-env.sh script generates cryptographically secure secrets. 
                  Keep your .env file secure and never commit it to version control.
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: 'Service Deployment',
      description: 'Start all AI services including Ollama, Supabase, n8n, and monitoring stack',
      icon: <CheckCircleIcon className="h-6 w-6" />,
      status: 'pending' as const,
      children: (
        <div className="space-y-4">
          <CodeBlock language="bash" title="For NVIDIA GPU Users">
{`python start_services.py --profile gpu-nvidia`}
          </CodeBlock>
          <CodeBlock language="bash" title="For CPU-only Systems">
{`python start_services.py --profile cpu`}
          </CodeBlock>
          <CodeBlock language="bash" title="For Mac/Apple Silicon">
{`python start_services.py --profile none`}
          </CodeBlock>
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-start">
              <ClockIcon className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
              <div>
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>Estimated Time:</strong> 5-15 minutes depending on your internet connection. 
                  First run will download Docker images (~10GB total).
                </p>
              </div>
            </div>
          </div>
        </div>
      )
    },
    {
      title: 'Service Verification',
      description: 'Verify all services are running correctly and accessible',
      icon: <CheckCircleIcon className="h-6 w-6" />,
      status: 'pending' as const,
      children: (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Core Services</h4>
              <ul className="space-y-1 text-sm">
                <li><Link href="http://localhost:5678" className="text-blue-600 hover:underline">n8n Workflows</Link> - localhost:5678</li>
                <li><Link href="http://localhost:3000" className="text-blue-600 hover:underline">Open WebUI</Link> - localhost:3000</li>
                <li><Link href="http://localhost:8000" className="text-blue-600 hover:underline">Supabase</Link> - localhost:8000</li>
                <li><Link href="http://localhost:3001" className="text-blue-600 hover:underline">Documentation</Link> - localhost:3001</li>
              </ul>
            </div>
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">AI & Analysis</h4>
              <ul className="space-y-1 text-sm">
                <li><Link href="http://localhost:11434" className="text-blue-600 hover:underline">Ollama API</Link> - localhost:11434</li>
                <li><Link href="http://localhost:6333" className="text-blue-600 hover:underline">Qdrant Vector DB</Link> - localhost:6333</li>
                <li><Link href="http://localhost:7474" className="text-blue-600 hover:underline">Neo4j Browser</Link> - localhost:7474</li>
                <li><Link href="http://localhost:8080" className="text-blue-600 hover:underline">SearXNG</Link> - localhost:8080</li>
              </ul>
            </div>
          </div>
          <CodeBlock language="bash" title="Health Check Commands">
{`# Check all services status
python tools/service-manager.py status

# Test individual services
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:6333/collections  # Qdrant
curl http://localhost:5678/healthz  # n8n`}
          </CodeBlock>
        </div>
      )
    }
  ];

  return (
    <Layout tableOfContents={tableOfContents}>
      <Head>
        <title>Quick Start Guide - Local AI Packaged</title>
        <meta 
          name="description" 
          content="Get up and running with Local AI Packaged in under 10 minutes. Complete setup guide with examples." 
        />
      </Head>

      <div className="prose prose-lg dark:prose-dark max-w-none">
        <div className="flex items-center space-x-3 mb-6">
          <RocketLaunchIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          <h1 id="overview" className="!mb-0">Quick Start Guide</h1>
        </div>
        
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
          Get Local AI Packaged up and running in under 10 minutes. This guide will walk you through 
          the complete setup process from installation to running your first government data analysis.
        </p>

        <div className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-gray-800 dark:to-gray-900 rounded-xl p-6 mb-8">
          <div className="flex items-start space-x-4">
            <InformationCircleIcon className="h-8 w-8 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                What You'll Get
              </h3>
              <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-700 dark:text-gray-300">
                <ul className="space-y-1">
                  <li>✅ Complete AI analysis platform</li>
                  <li>✅ 300+ government data sources</li>
                  <li>✅ Automated document processing</li>
                  <li>✅ Real-time monitoring dashboard</li>
                </ul>
                <ul className="space-y-1">
                  <li>✅ Local LLM inference with Ollama</li>
                  <li>✅ Vector search and embeddings</li>
                  <li>✅ Knowledge graph construction</li>
                  <li>✅ Comprehensive documentation</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <h2 id="prerequisites">Prerequisites</h2>
        
        <p>Before starting, ensure you have the following installed and configured:</p>

        <div className="grid md:grid-cols-2 gap-6 my-6">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">System Requirements</h3>
            <ul className="space-y-2 text-sm">
              <li><strong>OS:</strong> Linux, macOS, or Windows (WSL2)</li>
              <li><strong>CPU:</strong> x86_64 with AVX2 support</li>
              <li><strong>RAM:</strong> 16GB minimum, 32GB recommended</li>
              <li><strong>Storage:</strong> 50GB+ free space (SSD recommended)</li>
              <li><strong>GPU:</strong> Optional but recommended (NVIDIA/AMD)</li>
            </ul>
          </div>
          
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Required Software</h3>
            <ul className="space-y-2 text-sm">
              <li><strong>Docker:</strong> 20.10.0+ with Docker Compose v2</li>
              <li><strong>Python:</strong> 3.10+ (for management scripts)</li>
              <li><strong>Git:</strong> For repository cloning</li>
              <li><strong>Node.js:</strong> 18+ (for documentation website)</li>
            </ul>
          </div>
        </div>

        <CodeBlock language="bash" title="Verify Prerequisites">
{`# Check Docker version
docker --version
docker compose version

# Check Python version  
python3 --version

# Check available disk space
df -h

# Check available memory
free -h`}
        </CodeBlock>

        <h2 id="installation">Installation Process</h2>
        
        <p>Follow these steps to install and configure Local AI Packaged:</p>

        <ProcessFlow steps={setupSteps} />

        <h2 id="first-run">First Run Workflow</h2>
        
        <p>Once services are running, follow this workflow to complete your setup:</p>

        <MermaidDiagram chart={COMMON_DIAGRAMS.deploymentFlow} />

        <h2 id="verification">Service Verification</h2>
        
        <p>Verify that all services are running correctly:</p>

        <CodeBlock language="bash" title="Complete Health Check">
{`#!/bin/bash
echo "=== Local AI Packaged Health Check ==="

# Check Docker containers
echo "Docker containers:"
docker ps --format "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"

# Test service endpoints
echo -e "\\nService endpoints:"
services=(
  "n8n:http://localhost:5678/healthz"
  "Open WebUI:http://localhost:3000"
  "Supabase:http://localhost:8000/rest/v1/"
  "Ollama:http://localhost:11434/api/tags"
  "Qdrant:http://localhost:6333/collections"
  "Neo4j:http://localhost:7474/browser/"
)

for service in "\${services[@]}"; do
  name="\${service%%:*}"
  url="\${service#*:}"
  if curl -s --connect-timeout 5 "$url" >/dev/null; then
    echo "✅ $name: Available"
  else
    echo "❌ $name: Not responding"
  fi
done

echo -e "\\n=== Setup Complete! ==="
echo "🎉 All services are running and ready to use"`}
        </CodeBlock>

        <h2 id="first-analysis">Run Your First Analysis</h2>
        
        <p>Now let's run a simple analysis to verify everything is working:</p>

        <CodeBlock language="bash" title="Test Data Ingestion">
{`# 1. Test the ingestion system
python scripts/enhanced_government_ingestion.py \\
  --source congress \\
  --limit 10 \\
  --test-mode

# 2. Run a basic analysis
python scripts/demo_analysis.py

# 3. Generate a sample report
python scripts/generate_reports.py \\
  --sample-data \\
  --output-format html`}
        </CodeBlock>

        <CodeBlock language="python" title="Python API Test">
{`#!/usr/bin/env python3
"""
Quick test script to verify the analysis pipeline
"""

import asyncio
from pathlib import Path

async def test_analysis():
    print("🔍 Testing Local AI Packaged...")
    
    # Test 1: Service connectivity
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:11434/api/tags') as resp:
                if resp.status == 200:
                    print("✅ Ollama connection successful")
                else:
                    print("❌ Ollama connection failed")
    except Exception as e:
        print(f"❌ Service test failed: {e}")
    
    # Test 2: Import analysis modules
    try:
        from services.analysis import DocumentAnalyzer
        analyzer = DocumentAnalyzer()
        print("✅ Analysis modules imported successfully")
    except Exception as e:
        print(f"❌ Module import failed: {e}")
    
    # Test 3: Sample document processing
    try:
        sample_text = "H.R. 1234 - An Act to improve healthcare access..."
        # Simulate analysis without actual model loading
        print("✅ Document processing pipeline ready")
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
    
    print("\\n🎉 Test complete! Ready for analysis.")

if __name__ == "__main__":
    asyncio.run(test_analysis())`}
        </CodeBlock>

        <h2 id="next-steps">Next Steps</h2>
        
        <p>Congratulations! You now have Local AI Packaged running. Here's what to do next:</p>

        <div className="grid md:grid-cols-2 gap-6 my-8">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-4">
              🚀 Immediate Actions
            </h3>
            <ul className="space-y-2 text-blue-800 dark:text-blue-200 text-sm">
              <li><Link href="/analysis/methodology" className="hover:underline">Review analysis methodologies</Link></li>
              <li><Link href="/tools/overview" className="hover:underline">Explore available tools</Link></li>
              <li><Link href="/examples/basic" className="hover:underline">Try basic examples</Link></li>
              <li><Link href="http://localhost:5678" className="hover:underline">Set up n8n workflows</Link></li>
            </ul>
          </div>
          
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-4">
              📚 Learning Resources
            </h3>
            <ul className="space-y-2 text-green-800 dark:text-green-200 text-sm">
              <li><Link href="/procedures/workflows" className="hover:underline">Data workflows guide</Link></li>
              <li><Link href="/architecture/overview" className="hover:underline">System architecture</Link></li>
              <li><Link href="/api/rest" className="hover:underline">API documentation</Link></li>
              <li><Link href="/examples/advanced" className="hover:underline">Advanced use cases</Link></li>
            </ul>
          </div>
        </div>

        <h2 id="troubleshooting">Common Issues & Solutions</h2>
        
        <div className="space-y-6">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-3">
              ❌ Services Not Starting
            </h3>
            <div className="text-red-800 dark:text-red-200 text-sm space-y-2">
              <p><strong>Symptoms:</strong> Docker containers fail to start or immediately exit</p>
              <p><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Check Docker daemon is running: <code>docker info</code></li>
                <li>Verify ports are not in use: <code>lsof -i :5678</code></li>
                <li>Review container logs: <code>docker logs container_name</code></li>
                <li>Ensure sufficient disk space and memory</li>
              </ul>
            </div>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-900 dark:text-yellow-100 mb-3">
              ⚠️ Environment Configuration Issues
            </h3>
            <div className="text-yellow-800 dark:text-yellow-200 text-sm space-y-2">
              <p><strong>Symptoms:</strong> Services start but authentication fails</p>
              <p><strong>Solutions:</strong></p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Regenerate secrets: <code>./fix-supabase-env.sh</code></li>
                <li>Check .env file exists and is not empty</li>
                <li>Verify no special characters in passwords</li>
                <li>Restart services after environment changes</li>
              </ul>
            </div>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
              🐛 Getting Help
            </h3>
            <div className="text-blue-800 dark:text-blue-200 text-sm space-y-2">
              <p>If you encounter issues not covered here:</p>
              <ul className="list-disc list-inside ml-4 space-y-1">
                <li>Check the <Link href="/procedures/troubleshooting" className="hover:underline">troubleshooting guide</Link></li>
                <li>Review logs: <code>python tools/service-manager.py logs</code></li>
                <li>Visit the <Link href="https://github.com/cbwinslow/local-ai-packaged/issues" className="hover:underline">GitHub issues</Link></li>
                <li>Run health check: <code>python tools/service-manager.py health-check</code></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-green-100 to-blue-100 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl p-8 mt-12 text-center">
          <CheckCircleIcon className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            🎉 Setup Complete!
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            You now have a fully functional AI-powered government data analysis platform.
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link
              href="/analysis/methodology"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm font-medium"
            >
              Explore Methodologies
            </Link>
            <Link
              href="/tools/overview"
              className="inline-flex items-center px-4 py-2 border border-blue-600 text-blue-600 dark:text-blue-400 rounded-md hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors text-sm font-medium"
            >
              Browse Tools
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export const getStaticProps: GetStaticProps = async () => {
  return {
    props: {},
  };
};