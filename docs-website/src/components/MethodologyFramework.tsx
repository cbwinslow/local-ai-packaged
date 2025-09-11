import React from 'react';
import { 
  DocumentMagnifyingGlassIcon, 
  ChartBarIcon, 
  CircleStackIcon, 
  CpuChipIcon,
  BeakerIcon,
  AcademicCapIcon
} from '@heroicons/react/24/outline';
import { CodeBlock } from './CodeBlock';

interface MethodologyCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  steps: string[];
  tools: string[];
  example?: React.ReactNode;
}

export function MethodologyCard({ title, description, icon, steps, tools, example }: MethodologyCardProps) {
  return (
    <div className="methodology-card">
      <div className="flex items-start space-x-4">
        <div className="flex-shrink-0 text-blue-600 dark:text-blue-400">
          {icon}
        </div>
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
            {title}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {description}
          </p>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Process Steps</h4>
              <ol className="space-y-2">
                {steps.map((step, index) => (
                  <li key={index} className="flex items-start space-x-3 text-sm">
                    <span className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium">
                      {index + 1}
                    </span>
                    <span className="text-gray-700 dark:text-gray-300">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
            
            <div>
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Tools & Libraries</h4>
              <div className="space-y-2">
                {tools.map((tool, index) => (
                  <div key={index} className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 mr-2 mb-2">
                    {tool}
                  </div>
                ))}
              </div>
            </div>
          </div>
          
          {example && (
            <div className="mt-6">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">Example Usage</h4>
              {example}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export function AnalysisMethodologies() {
  const methodologies = [
    {
      title: "Document Classification & Entity Recognition",
      description: "Automated classification of government documents and extraction of key entities such as legislation numbers, dates, organizations, and policy areas.",
      icon: <DocumentMagnifyingGlassIcon className="h-8 w-8" />,
      steps: [
        "Document preprocessing and text extraction",
        "Feature engineering with TF-IDF and embeddings",
        "Multi-class classification using ensemble methods",
        "Named entity recognition with custom models",
        "Validation and confidence scoring"
      ],
      tools: ["spaCy", "NLTK", "scikit-learn", "transformers", "PyTorch"],
      example: (
        <CodeBlock language="python" title="Document Classification Example">
{`from services.analysis import DocumentClassifier
from transformers import AutoTokenizer, AutoModel

# Initialize the classifier
classifier = DocumentClassifier(
    model_name="distilbert-base-uncased",
    categories=["bill", "amendment", "resolution", "report"]
)

# Classify a document
document_text = "H.R. 1234 - An Act to improve healthcare access..."
result = classifier.classify(document_text)

print(f"Category: {result.category}")
print(f"Confidence: {result.confidence:.3f}")
print(f"Entities: {result.entities}")`}
        </CodeBlock>
      )
    },
    {
      title: "Sentiment & Policy Impact Analysis",
      description: "Advanced sentiment analysis and policy impact assessment using transformer models fine-tuned on government documents.",
      icon: <ChartBarIcon className="h-8 w-8" />,
      steps: [
        "Text preprocessing and normalization",
        "Sentiment classification with BERT variants",
        "Policy impact scoring using domain models",
        "Temporal analysis and trend detection",
        "Stakeholder impact assessment"
      ],
      tools: ["transformers", "VADER", "TextBlob", "pandas", "matplotlib"],
      example: (
        <CodeBlock language="python" title="Sentiment Analysis Example">
{`from services.analysis import PolicySentimentAnalyzer

analyzer = PolicySentimentAnalyzer()

# Analyze policy document sentiment
policy_text = """The proposed legislation aims to reduce 
healthcare costs while improving access to essential services..."""

analysis = analyzer.analyze(policy_text)

print(f"Overall Sentiment: {analysis.sentiment}")
print(f"Stakeholder Impacts: {analysis.stakeholder_impacts}")
print(f"Policy Areas: {analysis.policy_areas}")`}
        </CodeBlock>
      )
    },
    {
      title: "Knowledge Graph Construction",
      description: "Building comprehensive knowledge graphs from government data to understand relationships between entities, policies, and outcomes.",
      icon: <CircleStackIcon className="h-8 w-8" />,
      steps: [
        "Entity extraction and resolution",
        "Relationship identification and classification",
        "Graph schema design and validation",
        "Neo4j integration and indexing",
        "Query optimization and visualization"
      ],
      tools: ["Neo4j", "spaCy", "networkx", "py2neo", "Cypher"],
      example: (
        <CodeBlock language="python" title="Knowledge Graph Example">
{`from services.graph import KnowledgeGraphBuilder
from neo4j import GraphDatabase

# Initialize graph builder
builder = KnowledgeGraphBuilder()

# Extract entities and relationships
entities = builder.extract_entities(document_text)
relationships = builder.identify_relationships(entities)

# Store in Neo4j
with GraphDatabase.driver(uri, auth=(user, password)) as driver:
    builder.create_nodes(driver, entities)
    builder.create_relationships(driver, relationships)

# Query the graph
result = builder.query(
    "MATCH (b:Bill)-[:AFFECTS]->(p:Policy) RETURN b.title, p.area"
)`}
        </CodeBlock>
      )
    },
    {
      title: "Automated Report Generation",
      description: "AI-powered generation of comprehensive analysis reports with visualizations, summaries, and actionable insights.",
      icon: <BeakerIcon className="h-8 w-8" />,
      steps: [
        "Data aggregation and preprocessing",
        "Statistical analysis and trend identification",
        "Visualization generation with Plotly/Matplotlib",
        "Natural language summary generation",
        "PDF/HTML report compilation"
      ],
      tools: ["Plotly", "matplotlib", "ReportLab", "Jinja2", "WeasyPrint"],
      example: (
        <CodeBlock language="python" title="Report Generation Example">
{`from services.reports import AnalysisReportGenerator

generator = AnalysisReportGenerator()

# Generate comprehensive report
report = generator.create_report(
    data_sources=["bills", "amendments", "voting_records"],
    analysis_types=["sentiment", "impact", "trends"],
    date_range=("2023-01-01", "2023-12-31"),
    output_format="pdf"
)

# Include visualizations
report.add_chart("sentiment_over_time", chart_type="line")
report.add_chart("policy_impact_heatmap", chart_type="heatmap")

# Generate and save
report.generate("government_analysis_2023.pdf")`}
        </CodeBlock>
      )
    }
  ];

  return (
    <div className="space-y-8">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          Government Data Analysis Methodologies
        </h2>
        <p className="text-lg text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
          Comprehensive frameworks for analyzing government documents, legislation, and policy data using advanced AI and machine learning techniques.
        </p>
      </div>

      <div className="grid gap-8">
        {methodologies.map((methodology, index) => (
          <MethodologyCard key={index} {...methodology} />
        ))}
      </div>

      <div className="mt-12 bg-gradient-to-r from-blue-50 to-indigo-100 dark:from-gray-800 dark:to-gray-900 rounded-xl p-8">
        <div className="flex items-start space-x-4">
          <AcademicCapIcon className="h-8 w-8 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-1" />
          <div>
            <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-3">
              Research & Academic Integration
            </h3>
            <p className="text-gray-700 dark:text-gray-300 mb-4">
              Our methodologies are based on peer-reviewed research and best practices from computational social science, 
              natural language processing, and policy analysis domains. We continuously update our approaches based on 
              the latest academic findings and real-world validation.
            </p>
            <div className="grid md:grid-cols-3 gap-4 text-sm">
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Data Sources</h4>
                <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                  <li>• Congress.gov API</li>
                  <li>• GovInfo.gov</li>
                  <li>• Federal Register</li>
                  <li>• State Legislature APIs</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Validation Methods</h4>
                <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                  <li>• Cross-validation testing</li>
                  <li>• Expert annotation verification</li>
                  <li>• Inter-annotator agreement</li>
                  <li>• A/B testing frameworks</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">Output Formats</h4>
                <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                  <li>• JSON structured data</li>
                  <li>• CSV for analysis</li>
                  <li>• PDF reports</li>
                  <li>• Interactive dashboards</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}