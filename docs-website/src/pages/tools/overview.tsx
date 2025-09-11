import React, { useState } from 'react';
import { GetStaticProps } from 'next';
import Head from 'next/head';
import { Layout } from '@/components/Layout';
import { AutoDocumentation } from '@/components/AutoDocumentation';
import { CodeBlock } from '@/components/CodeBlock';
import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/react/24/outline';

export default function ToolsOverviewPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState<'all' | 'functions' | 'classes' | 'modules'>('all');

  const tableOfContents = [
    { id: 'overview', title: 'Overview', level: 1 },
    { id: 'auto-docs', title: 'Auto-Generated Documentation', level: 1 },
    { id: 'search-filter', title: 'Search & Filter', level: 2 },
    { id: 'key-tools', title: 'Key Tools & Scripts', level: 1 },
    { id: 'ingestion-tools', title: 'Data Ingestion Tools', level: 2 },
    { id: 'analysis-tools', title: 'Analysis Tools', level: 2 },
    { id: 'utility-tools', title: 'Utility Tools', level: 2 },
    { id: 'usage-examples', title: 'Usage Examples', level: 1 },
  ];

  const keyTools = [
    {
      name: 'enhanced_government_ingestion.py',
      description: 'Comprehensive government data ingestion system supporting 300+ sources',
      category: 'Ingestion',
      features: ['Rate limiting', 'Document parsing', 'Error handling', 'Progress tracking'],
      example: `python scripts/enhanced_government_ingestion.py \\
  --source congress \\
  --limit 1000 \\
  --analysis-types sentiment,entities`
    },
    {
      name: 'generate_reports.py',
      description: 'Automated report generation with visualizations and analysis summaries',
      category: 'Analysis',
      features: ['PDF generation', 'Chart creation', 'Data aggregation', 'Template system'],
      example: `python scripts/generate_reports.py \\
  --output-format pdf \\
  --include-charts \\
  --date-range 2023-01-01,2023-12-31`
    },
    {
      name: 'service-manager.py',
      description: 'Service orchestration and management for the entire AI stack',
      category: 'Management',
      features: ['Service startup', 'Health checks', 'Log monitoring', 'Configuration'],
      example: `python tools/service-manager.py start
python tools/service-manager.py status
python tools/service-manager.py logs --service ollama`
    },
    {
      name: 'ai_tools_manager.sh',
      description: 'Docker-based AI services management and orchestration',
      category: 'Infrastructure',
      features: ['Container management', 'Volume handling', 'Network setup', 'Monitoring'],
      example: `./scripts/ai_tools_manager.sh start
./scripts/ai_tools_manager.sh status
./scripts/ai_tools_manager.sh logs neo4j`
    }
  ];

  return (
    <Layout tableOfContents={tableOfContents}>
      <Head>
        <title>Tools Overview - Local AI Packaged</title>
        <meta 
          name="description" 
          content="Comprehensive overview of all Python tools, scripts, and utilities in the Local AI Packaged repository." 
        />
      </Head>

      <div className="prose prose-lg dark:prose-dark max-w-none">
        <h1 id="overview">Python Tools & Scripts Overview</h1>
        
        <p className="text-xl text-gray-600 dark:text-gray-400 mb-8">
          This page provides a comprehensive overview of all Python tools, scripts, and utilities 
          available in the Local AI Packaged repository. Use the search and filtering capabilities 
          below to find specific functions, classes, or modules.
        </p>

        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 mb-8">
          <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
            🚀 Quick Start
          </h3>
          <p className="text-blue-800 dark:text-blue-200 mb-4">
            All tools are automatically documented from the source code. The documentation includes 
            function signatures, parameters, docstrings, and usage examples where available.
          </p>
          <CodeBlock language="bash" title="Generate Latest Documentation">
{`# Generate documentation from current codebase
cd docs-website
npm run generate-docs

# Or run manually
python scripts/generate_docs.py`}
          </CodeBlock>
        </div>

        <h2 id="key-tools">Key Tools & Scripts</h2>
        
        <p>
          Below are the most important tools and scripts in the repository, organized by category:
        </p>

        <div className="tool-showcase">
          {keyTools.map((tool, index) => (
            <div key={index} className="tool-card">
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                  {tool.name}
                </h3>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                  {tool.category}
                </span>
              </div>
              
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                {tool.description}
              </p>
              
              <div className="mb-4">
                <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">Features:</h4>
                <div className="flex flex-wrap gap-2">
                  {tool.features.map((feature, featureIndex) => (
                    <span key={featureIndex} className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
              
              <CodeBlock language="bash" showLineNumbers={false}>
                {tool.example}
              </CodeBlock>
            </div>
          ))}
        </div>

        <h2 id="auto-docs">Auto-Generated Documentation</h2>
        
        <p>
          The following documentation is automatically generated from the Python codebase. 
          It includes all functions, classes, and modules with their signatures, parameters, 
          and docstrings.
        </p>

        <h3 id="search-filter">Search & Filter Tools</h3>
        
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-8">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="sr-only">Search documentation</label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  id="search"
                  type="text"
                  placeholder="Search functions, classes, modules..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="block w-full pl-10 pr-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-500 focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <FunnelIcon className="h-5 w-5 text-gray-400" />
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value as any)}
                className="block px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="all">All Items</option>
                <option value="modules">Modules Only</option>
                <option value="functions">Functions Only</option>
                <option value="classes">Classes Only</option>
              </select>
            </div>
          </div>
          
          {searchTerm && (
            <div className="mt-3 text-sm text-gray-600 dark:text-gray-400">
              Searching for: <span className="font-medium">"{searchTerm}"</span>
            </div>
          )}
        </div>

        <AutoDocumentation searchTerm={searchTerm} category={category} />

        <h2 id="usage-examples">Usage Examples</h2>
        
        <p>
          Here are some common usage patterns and examples for working with the tools:
        </p>

        <h3 id="ingestion-tools">Data Ingestion Workflow</h3>
        
        <CodeBlock language="python" title="Complete Data Ingestion Example">
{`#!/usr/bin/env python3
"""
Example: Complete government data ingestion workflow
"""

import asyncio
from pathlib import Path
from services.ingestion import DataIngester
from services.analysis import AnalysisPipeline

async def main():
    # Initialize data ingester
    ingester = DataIngester(
        data_dir=Path("data/government"),
        rate_limit=1.0,  # 1 request per second
        max_workers=4
    )
    
    # Configure sources
    sources = [
        "congress.gov",
        "govinfo.gov", 
        "federalregister.gov"
    ]
    
    # Ingest data
    for source in sources:
        print(f"Ingesting from {source}...")
        await ingester.ingest_from_source(
            source=source,
            document_types=["bills", "amendments", "reports"],
            date_range=("2023-01-01", "2023-12-31"),
            limit=1000
        )
    
    # Run analysis pipeline
    pipeline = AnalysisPipeline()
    results = await pipeline.process_all(
        input_dir=Path("data/government"),
        analysis_types=["classification", "sentiment", "entities"]
    )
    
    print(f"Processed {len(results)} documents")
    return results

if __name__ == "__main__":
    asyncio.run(main())`}
        </CodeBlock>

        <h3 id="analysis-tools">Analysis & Report Generation</h3>
        
        <CodeBlock language="python" title="Analysis and Reporting Example">
{`#!/usr/bin/env python3
"""
Example: Generate comprehensive analysis report
"""

from services.analysis import DocumentAnalyzer
from services.reports import ReportGenerator
from datetime import datetime, timedelta

# Initialize analyzer
analyzer = DocumentAnalyzer(
    model_name="distilbert-base-uncased",
    enable_gpu=True
)

# Analyze documents
results = analyzer.analyze_batch(
    documents_path="data/government/bills/",
    analysis_types=[
        "classification",
        "sentiment", 
        "entity_recognition",
        "topic_modeling"
    ]
)

# Generate visualizations
visualizer = analyzer.create_visualizations(results)
charts = [
    visualizer.create_sentiment_timeline(),
    visualizer.create_topic_distribution(),
    visualizer.create_entity_network(),
    visualizer.create_policy_impact_heatmap()
]

# Generate comprehensive report
report_generator = ReportGenerator()
report = report_generator.create_report(
    title="Government Data Analysis Report",
    subtitle=f"Analysis Period: {datetime.now() - timedelta(days=365)} to {datetime.now()}",
    data=results,
    charts=charts,
    template="comprehensive"
)

# Export in multiple formats
report.export("report.pdf")
report.export("report.html")
report.export_data("report_data.json")

print("Report generated successfully!")`}
        </CodeBlock>

        <h3 id="utility-tools">Utility & Management Tools</h3>
        
        <CodeBlock language="bash" title="Service Management Commands">
{`#!/bin/bash
# Service management examples

# Start all services with GPU support
python tools/service-manager.py start --profile gpu-nvidia

# Check service health
python tools/service-manager.py health-check

# View logs for specific service
python tools/service-manager.py logs --service n8n --tail 100

# Restart a specific service
python tools/service-manager.py restart --service ollama

# Stop all services
python tools/service-manager.py stop

# Generate system report
python tools/service-manager.py report --output system_report.json`}
        </CodeBlock>

        <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-6 mt-8">
          <h4 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-3">
            💡 Pro Tips
          </h4>
          <ul className="space-y-2 text-green-800 dark:text-green-200">
            <li><strong>Auto-completion:</strong> Use tab completion for script parameters and options</li>
            <li><strong>Configuration:</strong> Most tools accept configuration via YAML files</li>
            <li><strong>Logging:</strong> All tools support verbose logging with <code>--verbose</code> flag</li>
            <li><strong>Parallel Processing:</strong> Use <code>--workers N</code> to specify number of parallel workers</li>
            <li><strong>Dry Run:</strong> Test commands with <code>--dry-run</code> flag before execution</li>
          </ul>
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