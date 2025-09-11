import React, { useEffect, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
}

export function MermaidDiagram({ chart, className }: MermaidDiagramProps) {
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const renderDiagram = async () => {
      try {
        mermaid.initialize({
          startOnLoad: false,
          theme: document.documentElement.classList.contains('dark') ? 'dark' : 'default',
          securityLevel: 'loose',
          fontFamily: 'ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", sans-serif',
        });

        const { svg: renderedSvg } = await mermaid.render('mermaid-' + Date.now(), chart);
        setSvg(renderedSvg);
        setError('');
      } catch (err) {
        console.error('Mermaid rendering error:', err);
        setError('Failed to render diagram');
      }
    };

    renderDiagram();

    // Re-render on theme change
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          renderDiagram();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, [chart]);

  if (error) {
    return (
      <div className={`workflow-diagram ${className || ''}`}>
        <div className="text-center py-8">
          <p className="text-red-600 dark:text-red-400">{error}</p>
          <details className="mt-4">
            <summary className="cursor-pointer text-sm text-gray-500 dark:text-gray-400">
              Show chart definition
            </summary>
            <pre className="mt-2 text-xs text-left bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-x-auto">
              {chart}
            </pre>
          </details>
        </div>
      </div>
    );
  }

  return (
    <div className={`workflow-diagram ${className || ''}`}>
      <div
        className="mermaid flex justify-center"
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </div>
  );
}

interface WorkflowStepProps {
  title: string;
  description: string;
  icon?: React.ReactNode;
  status?: 'pending' | 'active' | 'completed';
  children?: React.ReactNode;
}

export function WorkflowStep({ title, description, icon, status = 'pending', children }: WorkflowStepProps) {
  const statusColors = {
    pending: 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800',
    active: 'border-blue-200 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20',
    completed: 'border-green-200 dark:border-green-700 bg-green-50 dark:bg-green-900/20',
  };

  const iconColors = {
    pending: 'text-gray-400 dark:text-gray-500',
    active: 'text-blue-600 dark:text-blue-400',
    completed: 'text-green-600 dark:text-green-400',
  };

  return (
    <div className={`border rounded-lg p-6 ${statusColors[status]}`}>
      <div className="flex items-start space-x-4">
        {icon && (
          <div className={`flex-shrink-0 ${iconColors[status]}`}>
            {icon}
          </div>
        )}
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {title}
          </h3>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            {description}
          </p>
          {children && (
            <div className="mt-4">
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface ProcessFlowProps {
  steps: Array<{
    title: string;
    description: string;
    icon?: React.ReactNode;
    status?: 'pending' | 'active' | 'completed';
    children?: React.ReactNode;
  }>;
}

export function ProcessFlow({ steps }: ProcessFlowProps) {
  return (
    <div className="space-y-6">
      {steps.map((step, index) => (
        <div key={index} className="relative">
          {index < steps.length - 1 && (
            <div className="absolute left-6 top-16 w-0.5 h-12 bg-gray-200 dark:bg-gray-700 transform translate-x-2" />
          )}
          <WorkflowStep {...step} />
        </div>
      ))}
    </div>
  );
}

// Pre-defined diagrams for common workflows
export const COMMON_DIAGRAMS = {
  dataIngestion: `
    graph TD
      A[Government Data Sources] --> B[Rate Limited Scraper]
      B --> C[Document Parser]
      C --> D[Data Validator]
      D --> E[Database Storage]
      E --> F[Vector Embeddings]
      F --> G[Search Index]
      
      style A fill:#e1f5fe
      style G fill:#e8f5e8
  `,
  
  analysisWorkflow: `
    graph LR
      A[Raw Documents] --> B[Text Extraction]
      B --> C[Preprocessing]
      C --> D[NLP Analysis]
      D --> E[Entity Recognition]
      E --> F[Sentiment Analysis]
      F --> G[Topic Modeling]
      G --> H[Report Generation]
      
      style A fill:#fff3e0
      style H fill:#e8f5e8
  `,
  
  systemArchitecture: `
    graph TB
      subgraph "Frontend Layer"
        A[Next.js Docs Site]
        B[Dashboard UI]
        C[Open WebUI]
      end
      
      subgraph "API Layer"
        D[FastAPI Backend]
        E[n8n Workflows]
        F[Kong Gateway]
      end
      
      subgraph "Processing Layer"
        G[Data Ingestion]
        H[Analysis Engine]
        I[Queue System]
      end
      
      subgraph "Storage Layer"
        J[PostgreSQL]
        K[Qdrant Vector DB]
        L[Neo4j Graph DB]
      end
      
      subgraph "AI Services"
        M[Ollama LLMs]
        N[Embedding Models]
        O[Analysis Models]
      end
      
      A --> D
      B --> D
      C --> E
      D --> G
      D --> H
      E --> I
      G --> J
      H --> K
      H --> L
      H --> M
      G --> N
      H --> O
  `,
  
  deploymentFlow: `
    graph TD
      A[Clone Repository] --> B[Configure Environment]
      B --> C[Generate Secrets]
      C --> D[Start Supabase]
      D --> E[Start AI Services]
      E --> F[Deploy Applications]
      F --> G[Configure DNS]
      G --> H[Enable Monitoring]
      H --> I[Ready for Use]
      
      style A fill:#e3f2fd
      style I fill:#e8f5e8
  `
};