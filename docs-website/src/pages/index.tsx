import React from 'react';
import { GetStaticProps } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { Layout } from '@/components/Layout';
import { MermaidDiagram, COMMON_DIAGRAMS } from '@/components/Diagrams';
import { CodeBlock } from '@/components/CodeBlock';
import { 
  RocketLaunchIcon, 
  DocumentTextIcon, 
  CpuChipIcon, 
  CircleStackIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  BeakerIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';

export default function HomePage() {
  const features = [
    {
      name: 'AI-Powered Analysis',
      description: 'Advanced machine learning models for document classification, sentiment analysis, and entity recognition.',
      icon: CpuChipIcon,
      href: '/analysis/methodology',
    },
    {
      name: 'Comprehensive Data Sources',
      description: 'Ingestion from 300+ government sources including federal, state, and local data repositories.',
      icon: CircleStackIcon,
      href: '/analysis/data-sources',
    },
    {
      name: 'Automated Workflows',
      description: 'End-to-end automation from data ingestion to report generation with intelligent error handling.',
      icon: Cog6ToothIcon,
      href: '/procedures/workflows',
    },
    {
      name: 'Interactive Documentation',
      description: 'Searchable, comprehensive documentation with code examples and interactive tutorials.',
      icon: DocumentTextIcon,
      href: '/examples/basic',
    },
    {
      name: 'Real-time Monitoring',
      description: 'Built-in monitoring and observability stack with Prometheus, Grafana, and custom dashboards.',
      icon: ChartBarIcon,
      href: '/architecture/overview',
    },
    {
      name: 'Research Integration',
      description: 'Methodologies based on peer-reviewed research and validated through academic partnerships.',
      icon: AcademicCapIcon,
      href: '/analysis/methodology',
    },
  ];

  const quickStart = [
    {
      title: 'Install & Configure',
      description: 'Clone the repository and set up your environment in minutes.',
      code: `git clone https://github.com/cbwinslow/local-ai-packaged.git
cd local-ai-packaged
cp .env.example .env
./fix-supabase-env.sh`,
    },
    {
      title: 'Start Services',
      description: 'Launch the complete AI stack with Docker Compose.',
      code: `python start_services.py --profile gpu-nvidia
# Services available at:
# - n8n: http://localhost:5678
# - Open WebUI: http://localhost:3000
# - Documentation: http://localhost:3001`,
    },
    {
      title: 'Run Analysis',
      description: 'Start analyzing government data immediately.',
      code: `python scripts/enhanced_government_ingestion.py \\
  --source congress \\
  --limit 1000 \\
  --analysis-types sentiment,entities,classification

python scripts/generate_reports.py \\
  --output-format pdf`,
    },
  ];

  return (
    <Layout>
      <Head>
        <title>Local AI Packaged - Comprehensive Documentation</title>
        <meta 
          name="description" 
          content="Complete documentation for Local AI Packaged - Government data analysis platform with AI-powered insights, automated workflows, and comprehensive tooling." 
        />
      </Head>

      {/* Hero Section */}
      <div className="relative isolate px-6 pt-14 lg:px-8">
        <div className="mx-auto max-w-4xl py-12 sm:py-20">
          <div className="text-center">
            <div className="flex justify-center mb-8">
              <div className="relative">
                <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl flex items-center justify-center">
                  <span className="text-white font-bold text-3xl">LA</span>
                </div>
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs font-bold">✓</span>
                </div>
              </div>
            </div>
            <h1 className="text-4xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-6xl">
              Local AI Packaged
            </h1>
            <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-400">
              Comprehensive government data analysis platform with AI-powered insights, 
              automated workflows, and production-ready infrastructure. Built for researchers, 
              analysts, and organizations working with government data.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link
                href="/getting-started/quick-start"
                className="rounded-md bg-blue-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-colors"
              >
                <RocketLaunchIcon className="inline h-4 w-4 mr-2" />
                Get Started
              </Link>
              <Link
                href="/analysis/methodology" 
                className="text-sm font-semibold leading-6 text-gray-900 dark:text-gray-100 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
              >
                View Methodologies <span aria-hidden="true">→</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100 sm:text-4xl">
            Everything you need for government data analysis
          </h2>
          <p className="mt-6 text-lg leading-8 text-gray-600 dark:text-gray-400">
            From data ingestion to advanced AI analysis, our platform provides comprehensive tools 
            for understanding government operations, policy impacts, and legislative trends.
          </p>
        </div>
        <div className="mx-auto mt-16 max-w-6xl">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <Link key={feature.name} href={feature.href} className="group">
                <div className="relative overflow-hidden rounded-lg bg-white dark:bg-gray-800 p-8 shadow-sm ring-1 ring-gray-200 dark:ring-gray-700 hover:shadow-lg hover:ring-blue-300 dark:hover:ring-blue-600 transition-all">
                  <div>
                    <span className="inline-flex rounded-lg p-3 bg-blue-50 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 group-hover:bg-blue-100 dark:group-hover:bg-blue-900 transition-colors">
                      <feature.icon className="h-6 w-6" aria-hidden="true" />
                    </span>
                  </div>
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                      {feature.name}
                    </h3>
                    <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* System Architecture Diagram */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
            System Architecture
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Comprehensive overview of the Local AI Packaged platform architecture
          </p>
        </div>
        <MermaidDiagram chart={COMMON_DIAGRAMS.systemArchitecture} />
      </div>

      {/* Quick Start Section */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
            Quick Start Guide
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Get up and running with Local AI Packaged in minutes
          </p>
        </div>
        
        <div className="grid gap-8 lg:grid-cols-3">
          {quickStart.map((step, index) => (
            <div key={index} className="relative">
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                <div className="flex items-center mb-4">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">
                    {index + 1}
                  </div>
                  <h3 className="ml-3 text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {step.title}
                  </h3>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {step.description}
                </p>
                <CodeBlock language="bash" showLineNumbers={false}>
                  {step.code}
                </CodeBlock>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            href="/getting-started/installation"
            className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
          >
            <DocumentTextIcon className="mr-2 h-5 w-5" />
            View Full Installation Guide
          </Link>
        </div>
      </div>

      {/* What's Included */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="bg-gradient-to-r from-blue-50 to-indigo-100 dark:from-gray-800 dark:to-gray-900 rounded-2xl p-8 lg:p-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              What's Included
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
              Complete toolkit for government data analysis and AI workflows
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <BeakerIcon className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">AI Services</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ollama, n8n, Flowise, Langfuse</p>
            </div>
            
            <div className="text-center">
              <CircleStackIcon className="h-12 w-12 text-green-600 dark:text-green-400 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Databases</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">PostgreSQL, Neo4j, Qdrant, Redis</p>
            </div>
            
            <div className="text-center">
              <ChartBarIcon className="h-12 w-12 text-purple-600 dark:text-purple-400 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Monitoring</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Prometheus, Grafana, OpenSearch</p>
            </div>
            
            <div className="text-center">
              <DocumentTextIcon className="h-12 w-12 text-orange-600 dark:text-orange-400 mx-auto mb-4" />
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">Tools</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">Python Scripts, APIs, Dashboards</p>
            </div>
          </div>
        </div>
      </div>

      {/* Call to Action */}
      <div className="mx-auto max-w-7xl px-6 lg:px-8 py-12">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
            Ready to get started?
          </h2>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
            Explore our comprehensive documentation and start analyzing government data today.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-4">
            <Link
              href="/getting-started/quick-start"
              className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              Quick Start Guide
            </Link>
            <Link
              href="/analysis/methodology"
              className="inline-flex items-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-base font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              View Methodologies
            </Link>
            <Link
              href="/examples/basic"
              className="inline-flex items-center px-6 py-3 border border-gray-300 dark:border-gray-600 text-base font-medium rounded-md text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              See Examples
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