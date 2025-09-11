import React, { useState, useEffect } from 'react';
import { CodeBlock, InlineCode } from './CodeBlock';
import { ChevronDownIcon, ChevronRightIcon, CodeBracketIcon, Square3Stack3DIcon } from '@heroicons/react/24/outline';

interface DocumentationData {
  modules: Array<{
    name: string;
    file_path: string;
    docstring: string | null;
    functions: Array<{
      name: string;
      signature: string;
      docstring: string | null;
      file_path: string;
      line_number: number;
      parameters: Array<{
        name: string;
        annotation: string | null;
        default: string | null;
      }>;
      return_type: string | null;
      decorators: string[];
      is_async: boolean;
      examples: string[];
    }>;
    classes: Array<{
      name: string;
      docstring: string | null;
      file_path: string;
      line_number: number;
      methods: any[];
      properties: any[];
      inheritance: string[];
      decorators: string[];
    }>;
    constants: Array<{
      name: string;
      line_number: number;
      value: string;
    }>;
    imports: string[];
  }>;
  summary: {
    total_modules: number;
    total_functions: number;
    total_classes: number;
    total_constants: number;
  };
}

interface AutoDocsProps {
  searchTerm?: string;
  category?: 'all' | 'functions' | 'classes' | 'modules';
}

export function AutoDocumentation({ searchTerm = '', category = 'all' }: AutoDocsProps) {
  const [docsData, setDocsData] = useState<DocumentationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [filteredData, setFilteredData] = useState<DocumentationData | null>(null);

  useEffect(() => {
    // Load the auto-generated documentation
    import('@/data/documentation.json')
      .then((data) => {
        setDocsData(data.default);
        setLoading(false);
      })
      .catch((error) => {
        console.error('Failed to load documentation:', error);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!docsData) return;

    let filtered = { ...docsData };

    // Apply search filter
    if (searchTerm) {
      filtered.modules = docsData.modules.filter(module => {
        const matchesModule = module.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                            (module.docstring && module.docstring.toLowerCase().includes(searchTerm.toLowerCase()));
        
        const matchingFunctions = module.functions.filter(func =>
          func.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (func.docstring && func.docstring.toLowerCase().includes(searchTerm.toLowerCase()))
        );
        
        const matchingClasses = module.classes.filter(cls =>
          cls.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          (cls.docstring && cls.docstring.toLowerCase().includes(searchTerm.toLowerCase()))
        );

        if (matchesModule || matchingFunctions.length > 0 || matchingClasses.length > 0) {
          // Return module with filtered functions and classes
          return {
            ...module,
            functions: matchingFunctions,
            classes: matchingClasses
          };
        }
        return false;
      }).filter(Boolean);
    }

    // Apply category filter
    if (category !== 'all') {
      filtered.modules = filtered.modules.map(module => ({
        ...module,
        functions: category === 'functions' ? module.functions : [],
        classes: category === 'classes' ? module.classes : [],
      })).filter(module => 
        (category === 'modules') ||
        (category === 'functions' && module.functions.length > 0) ||
        (category === 'classes' && module.classes.length > 0)
      );
    }

    setFilteredData(filtered);
  }, [docsData, searchTerm, category]);

  const toggleModule = (moduleName: string) => {
    const newExpanded = new Set(expandedModules);
    if (newExpanded.has(moduleName)) {
      newExpanded.delete(moduleName);
    } else {
      newExpanded.add(moduleName);
    }
    setExpandedModules(newExpanded);
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
        <div className="space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-100 dark:bg-gray-800 rounded"></div>
          ))}
        </div>
      </div>
    );
  }

  if (!filteredData) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 dark:text-gray-400">
          Failed to load documentation. Please ensure the documentation has been generated.
        </p>
        <CodeBlock language="bash" title="Generate Documentation">
          npm run generate-docs
        </CodeBlock>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            {filteredData.summary.total_modules}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Modules</div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {filteredData.summary.total_functions}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Functions</div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
            {filteredData.summary.total_classes}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Classes</div>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
            {filteredData.summary.total_constants}
          </div>
          <div className="text-sm text-gray-600 dark:text-gray-400">Constants</div>
        </div>
      </div>

      {/* Modules */}
      <div className="space-y-4">
        {filteredData.modules.map((module) => (
          <ModuleCard
            key={module.name}
            module={module}
            isExpanded={expandedModules.has(module.name)}
            onToggle={() => toggleModule(module.name)}
            searchTerm={searchTerm}
          />
        ))}
      </div>

      {filteredData.modules.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            No modules found matching your criteria.
          </p>
          {searchTerm && (
            <p className="text-sm text-gray-400 dark:text-gray-500">
              Try adjusting your search term: "{searchTerm}"
            </p>
          )}
        </div>
      )}
    </div>
  );
}

interface ModuleCardProps {
  module: any;
  isExpanded: boolean;
  onToggle: () => void;
  searchTerm: string;
}

function ModuleCard({ module, isExpanded, onToggle, searchTerm }: ModuleCardProps) {
  const highlightText = (text: string) => {
    if (!searchTerm) return text;
    
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) =>
      regex.test(part) ? (
        <span key={index} className="search-highlight">
          {part}
        </span>
      ) : (
        part
      )
    );
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
      <div
        className="p-6 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Square3Stack3DIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {highlightText(module.name)}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {module.file_path}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              {module.functions.length} functions
            </span>
            <span className="text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
              {module.classes.length} classes
            </span>
            {isExpanded ? (
              <ChevronDownIcon className="h-5 w-5 text-gray-400" />
            ) : (
              <ChevronRightIcon className="h-5 w-5 text-gray-400" />
            )}
          </div>
        </div>
        
        {module.docstring && (
          <p className="mt-3 text-gray-600 dark:text-gray-400 text-sm">
            {highlightText(module.docstring)}
          </p>
        )}
      </div>

      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-gray-700 p-6 space-y-6">
          {/* Functions */}
          {module.functions.length > 0 && (
            <div>
              <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                <CodeBracketIcon className="h-5 w-5 mr-2 text-green-600 dark:text-green-400" />
                Functions ({module.functions.length})
              </h4>
              <div className="space-y-4">
                {module.functions.map((func: any, index: number) => (
                  <FunctionCard key={index} func={func} searchTerm={searchTerm} />
                ))}
              </div>
            </div>
          )}

          {/* Classes */}
          {module.classes.length > 0 && (
            <div>
              <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3 flex items-center">
                <Square3Stack3DIcon className="h-5 w-5 mr-2 text-purple-600 dark:text-purple-400" />
                Classes ({module.classes.length})
              </h4>
              <div className="space-y-4">
                {module.classes.map((cls: any, index: number) => (
                  <ClassCard key={index} cls={cls} searchTerm={searchTerm} />
                ))}
              </div>
            </div>
          )}

          {/* Constants */}
          {module.constants.length > 0 && (
            <div>
              <h4 className="text-md font-semibold text-gray-900 dark:text-gray-100 mb-3">
                Constants ({module.constants.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {module.constants.map((constant: any, index: number) => (
                  <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded p-3">
                    <InlineCode>{constant.name}</InlineCode>
                    <span className="text-sm text-gray-500 dark:text-gray-400 ml-2">
                      Line {constant.line_number}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function FunctionCard({ func, searchTerm }: { func: any; searchTerm: string }) {
  const highlightText = (text: string) => {
    if (!searchTerm) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, index) =>
      regex.test(part) ? (
        <span key={index} className="search-highlight">{part}</span>
      ) : part
    );
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <h5 className="font-mono text-sm font-semibold text-gray-900 dark:text-gray-100">
          {highlightText(func.name)}
        </h5>
        <div className="flex space-x-1">
          {func.is_async && (
            <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded">
              async
            </span>
          )}
          {func.decorators.length > 0 && (
            <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded">
              decorated
            </span>
          )}
        </div>
      </div>
      
      <CodeBlock language="python" showLineNumbers={false}>
        {func.signature}
      </CodeBlock>
      
      {func.docstring && (
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          {highlightText(func.docstring)}
        </p>
      )}
      
      <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
        {func.file_path}:{func.line_number}
      </div>
    </div>
  );
}

function ClassCard({ cls, searchTerm }: { cls: any; searchTerm: string }) {
  const highlightText = (text: string) => {
    if (!searchTerm) return text;
    const regex = new RegExp(`(${searchTerm})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, index) =>
      regex.test(part) ? (
        <span key={index} className="search-highlight">{part}</span>
      ) : part
    );
  };

  return (
    <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <h5 className="font-mono text-sm font-semibold text-gray-900 dark:text-gray-100">
          {highlightText(cls.name)}
        </h5>
        <span className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
          {cls.methods.length} methods
        </span>
      </div>
      
      {cls.inheritance.length > 0 && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          Inherits from: {cls.inheritance.join(', ')}
        </p>
      )}
      
      {cls.docstring && (
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
          {highlightText(cls.docstring)}
        </p>
      )}
      
      <div className="text-xs text-gray-500 dark:text-gray-400">
        {cls.file_path}:{cls.line_number}
      </div>
    </div>
  );
}