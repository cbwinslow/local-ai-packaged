import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus, vs } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { ClipboardIcon, CheckIcon } from '@heroicons/react/24/outline';

interface CodeBlockProps {
  children: string;
  language?: string;
  title?: string;
  showLineNumbers?: boolean;
  className?: string;
}

export function CodeBlock({ children, language = 'text', title, showLineNumbers = true, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [isDark, setIsDark] = useState(() => 
    typeof window !== 'undefined' && document.documentElement.classList.contains('dark')
  );

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(children.trim());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  React.useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.attributeName === 'class') {
          setIsDark(document.documentElement.classList.contains('dark'));
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['class'],
    });

    return () => observer.disconnect();
  }, []);

  return (
    <div className={`code-block-container ${className || ''}`}>
      {title && (
        <div className="code-block-header">
          <span>{title}</span>
          <button onClick={copyToClipboard} className="copy-button">
            {copied ? (
              <CheckIcon className="h-4 w-4" />
            ) : (
              <ClipboardIcon className="h-4 w-4" />
            )}
          </button>
        </div>
      )}
      <div className="relative">
        {!title && (
          <button
            onClick={copyToClipboard}
            className="absolute top-2 right-2 z-10 p-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition-colors"
          >
            {copied ? (
              <CheckIcon className="h-4 w-4" />
            ) : (
              <ClipboardIcon className="h-4 w-4" />
            )}
          </button>
        )}
        <SyntaxHighlighter
          language={language}
          style={isDark ? vscDarkPlus : vs}
          showLineNumbers={showLineNumbers}
          customStyle={{
            margin: 0,
            borderRadius: title ? '0 0 0.5rem 0.5rem' : '0.5rem',
            background: isDark ? '#1f2937' : '#f9fafb',
          }}
          codeTagProps={{
            style: {
              fontSize: '0.875rem',
              fontFamily: 'ui-monospace, SFMono-Regular, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            },
          }}
        >
          {children.trim()}
        </SyntaxHighlighter>
      </div>
    </div>
  );
}

interface InlineCodeProps {
  children: React.ReactNode;
  className?: string;
}

export function InlineCode({ children, className }: InlineCodeProps) {
  return (
    <code className={`inline-flex items-center px-2 py-1 text-sm font-mono bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-md ${className || ''}`}>
      {children}
    </code>
  );
}

interface ApiEndpointProps {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
  endpoint: string;
  description?: string;
}

export function ApiEndpoint({ method, endpoint, description }: ApiEndpointProps) {
  const methodColors = {
    GET: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
    POST: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
    PUT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200',
    DELETE: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
    PATCH: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 my-4">
      <div className="flex items-center space-x-3">
        <span className={`px-2 py-1 text-xs font-semibold rounded ${methodColors[method]}`}>
          {method}
        </span>
        <InlineCode className="flex-1">{endpoint}</InlineCode>
      </div>
      {description && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {description}
        </p>
      )}
    </div>
  );
}

interface ParameterTableProps {
  parameters: Array<{
    name: string;
    type: string;
    required?: boolean;
    description: string;
    default?: string;
  }>;
}

export function ParameterTable({ parameters }: ParameterTableProps) {
  return (
    <div className="overflow-x-auto my-6">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Parameter
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Type
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Required
            </th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
              Description
            </th>
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
          {parameters.map((param, index) => (
            <tr key={index}>
              <td className="px-6 py-4 whitespace-nowrap">
                <InlineCode>{param.name}</InlineCode>
              </td>
              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                {param.type}
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                {param.required ? (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                    Required
                  </span>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200">
                    Optional
                  </span>
                )}
              </td>
              <td className="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                {param.description}
                {param.default && (
                  <span className="block mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Default: <InlineCode>{param.default}</InlineCode>
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}