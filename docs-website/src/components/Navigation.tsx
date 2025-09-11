import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { ChevronDownIcon, ChevronRightIcon, MagnifyingGlassIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';

interface NavigationItem {
  title: string;
  href?: string;
  children?: NavigationItem[];
  icon?: React.ComponentType<{ className?: string }>;
}

const navigation: NavigationItem[] = [
  {
    title: 'Getting Started',
    children: [
      { title: 'Overview', href: '/' },
      { title: 'Quick Start', href: '/getting-started/quick-start' },
      { title: 'Installation', href: '/getting-started/installation' },
      { title: 'Configuration', href: '/getting-started/configuration' },
    ],
  },
  {
    title: 'Government Data Analysis',
    children: [
      { title: 'Methodology Framework', href: '/analysis/methodology' },
      { title: 'Data Sources', href: '/analysis/data-sources' },
      { title: 'Ingestion Process', href: '/analysis/ingestion' },
      { title: 'Processing Pipeline', href: '/analysis/pipeline' },
      { title: 'Analysis Tools', href: '/analysis/tools' },
    ],
  },
  {
    title: 'Python Tools & Scripts',
    children: [
      { title: 'Tool Overview', href: '/tools/overview' },
      { title: 'Data Ingestion', href: '/tools/ingestion' },
      { title: 'Processing Scripts', href: '/tools/processing' },
      { title: 'Analysis Frameworks', href: '/tools/frameworks' },
      { title: 'Utility Functions', href: '/tools/utilities' },
    ],
  },
  {
    title: 'Services & Architecture',
    children: [
      { title: 'System Architecture', href: '/architecture/overview' },
      { title: 'Docker Services', href: '/architecture/docker' },
      { title: 'API Services', href: '/architecture/api' },
      { title: 'Database Schema', href: '/architecture/database' },
      { title: 'Queue System', href: '/architecture/queue' },
    ],
  },
  {
    title: 'Procedures & Workflows',
    children: [
      { title: 'Standard Procedures', href: '/procedures/standard' },
      { title: 'Data Workflows', href: '/procedures/workflows' },
      { title: 'Deployment Process', href: '/procedures/deployment' },
      { title: 'Troubleshooting', href: '/procedures/troubleshooting' },
    ],
  },
  {
    title: 'API Reference',
    children: [
      { title: 'REST APIs', href: '/api/rest' },
      { title: 'GraphQL', href: '/api/graphql' },
      { title: 'Webhooks', href: '/api/webhooks' },
      { title: 'Authentication', href: '/api/auth' },
    ],
  },
  {
    title: 'Examples & Tutorials',
    children: [
      { title: 'Basic Examples', href: '/examples/basic' },
      { title: 'Advanced Use Cases', href: '/examples/advanced' },
      { title: 'Integration Guides', href: '/examples/integration' },
      { title: 'Best Practices', href: '/examples/best-practices' },
    ],
  },
];

interface SidebarProps {
  className?: string;
}

export function Sidebar({ className }: SidebarProps) {
  const router = useRouter();
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({});

  useEffect(() => {
    // Auto-expand sections based on current route
    const currentPath = router.asPath;
    const newExpanded: Record<string, boolean> = {};
    
    navigation.forEach((section) => {
      if (section.children) {
        const hasActiveChild = section.children.some(child => child.href === currentPath);
        if (hasActiveChild) {
          newExpanded[section.title] = true;
        }
      }
    });
    
    setExpandedSections(prev => ({ ...prev, ...newExpanded }));
  }, [router.asPath]);

  const toggleSection = (title: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [title]: !prev[title]
    }));
  };

  return (
    <nav className={`${className} custom-scrollbar`}>
      <div className="nav-tree">
        {navigation.map((section) => (
          <div key={section.title}>
            {section.href ? (
              <Link
                href={section.href}
                className={`nav-tree-item parent ${
                  router.asPath === section.href ? 'active' : ''
                }`}
              >
                {section.title}
              </Link>
            ) : (
              <button
                onClick={() => toggleSection(section.title)}
                className="nav-tree-item parent w-full text-left flex items-center justify-between"
              >
                <span>{section.title}</span>
                {expandedSections[section.title] ? (
                  <ChevronDownIcon className="h-4 w-4" />
                ) : (
                  <ChevronRightIcon className="h-4 w-4" />
                )}
              </button>
            )}
            
            {section.children && expandedSections[section.title] && (
              <div className="ml-2 space-y-1">
                {section.children.map((child) => (
                  <Link
                    key={child.href}
                    href={child.href || '#'}
                    className={`nav-tree-item child ${
                      router.asPath === child.href ? 'active' : ''
                    }`}
                  >
                    {child.title}
                  </Link>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}

interface HeaderProps {
  onSearchOpen: () => void;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

export function Header({ onSearchOpen, darkMode, toggleDarkMode }: HeaderProps) {
  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">LA</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  Local AI Packaged
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Comprehensive Documentation
                </p>
              </div>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <button
              onClick={onSearchOpen}
              className="flex items-center space-x-2 px-3 py-2 text-sm text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded-md hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
            >
              <MagnifyingGlassIcon className="h-4 w-4" />
              <span>Search...</span>
              <kbd className="hidden sm:inline-flex items-center px-2 py-1 border border-gray-200 dark:border-gray-600 rounded text-xs bg-white dark:bg-gray-700">
                ⌘K
              </kbd>
            </button>

            <button
              onClick={toggleDarkMode}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            >
              {darkMode ? (
                <SunIcon className="h-5 w-5" />
              ) : (
                <MoonIcon className="h-5 w-5" />
              )}
            </button>

            <Link
              href="https://github.com/cbwinslow/local-ai-packaged"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
            >
              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z"
                  clipRule="evenodd"
                />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}

export { navigation };