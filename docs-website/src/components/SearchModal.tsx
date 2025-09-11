import React, { useState, useEffect, Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { MagnifyingGlassIcon, XMarkIcon, DocumentTextIcon, CodeBracketIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';
import Fuse from 'fuse.js';

interface SearchResult {
  title: string;
  content: string;
  url: string;
  type: 'page' | 'function' | 'class' | 'variable' | 'procedure';
  category: string;
}

// Load search data dynamically from an API endpoint or static JSON file
const [searchData, setSearchData] = useState<SearchResult[]>([]);
const [loading, setLoading] = useState<boolean>(true);

useEffect(() => {
  // Replace '/api/searchData' with your actual endpoint or static file path
  fetch('/api/searchData')
    .then((res) => res.json())
    .then((data) => {
      setSearchData(data);
      setLoading(false);
    })
    .catch((err) => {
      console.error('Failed to load search data:', err);
      setLoading(false);
    });
}, []);

// Initialize Fuse.js with dynamic searchData
const [fuse, setFuse] = useState<Fuse<SearchResult> | null>(null);

useEffect(() => {
  if (searchData.length > 0) {
    setFuse(
      new Fuse(searchData, {
        keys: ['title', 'content', 'category'],
        threshold: 0.4,
        includeScore: true,
      })
    );
  }
}, [searchData]);
interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  useEffect(() => {
    if (query.trim()) {
      const searchResults = fuse.search(query).map(result => result.item);
      setResults(searchResults);
      setSelectedIndex(0);
    } else {
      setResults([]);
    }
  }, [query]);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      window.location.href = results[selectedIndex].url;
      onClose();
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'page':
        return <DocumentTextIcon className="h-4 w-4" />;
      case 'function':
      case 'class':
        return <CodeBracketIcon className="h-4 w-4" />;
      case 'procedure':
        return <Cog6ToothIcon className="h-4 w-4" />;
      default:
        return <DocumentTextIcon className="h-4 w-4" />;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'page':
        return 'text-blue-600 dark:text-blue-400';
      case 'function':
        return 'text-green-600 dark:text-green-400';
      case 'class':
        return 'text-purple-600 dark:text-purple-400';
      case 'procedure':
        return 'text-orange-600 dark:text-orange-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-gray-500 bg-opacity-25 transition-opacity" />
        </Transition.Child>

        <div className="fixed inset-0 z-10 overflow-y-auto p-4 sm:p-6 md:p-20">
          <Transition.Child
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <Dialog.Panel className="mx-auto max-w-2xl transform divide-y divide-gray-100 dark:divide-gray-700 overflow-hidden rounded-xl bg-white dark:bg-gray-800 shadow-2xl ring-1 ring-black ring-opacity-5 transition-all">
              <div className="relative">
                <MagnifyingGlassIcon className="pointer-events-none absolute left-4 top-3.5 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  className="h-12 w-full border-0 bg-transparent pl-11 pr-4 text-gray-900 dark:text-gray-100 placeholder:text-gray-400 focus:ring-0 sm:text-sm"
                  placeholder="Search documentation..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  autoFocus
                />
                <button
                  onClick={onClose}
                  className="absolute right-4 top-3.5 h-5 w-5 text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon className="h-5 w-5" />
                </button>
              </div>

              {results.length > 0 && (
                <div className="max-h-80 overflow-y-auto py-2">
                  {results.map((result, index) => (
                    <Link
                      key={result.url}
                      href={result.url}
                      onClick={onClose}
                      className={`block px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 ${
                        index === selectedIndex ? 'bg-gray-50 dark:bg-gray-700' : ''
                      }`}
                    >
                      <div className="flex items-start space-x-3">
                        <div className={`mt-1 ${getTypeColor(result.type)}`}>
                          {getTypeIcon(result.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2">
                            <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                              {result.title}
                            </p>
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${getTypeColor(result.type)} bg-gray-100 dark:bg-gray-700`}>
                              {result.type}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                            {result.content}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                            {result.category}
                          </p>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}

              {query && results.length === 0 && (
                <div className="px-6 py-14 text-center text-sm sm:px-14">
                  <DocumentTextIcon className="mx-auto h-6 w-6 text-gray-400" />
                  <p className="mt-4 font-semibold text-gray-900 dark:text-gray-100">
                    No results found
                  </p>
                  <p className="mt-2 text-gray-500 dark:text-gray-400">
                    Try adjusting your search terms or browse the navigation menu.
                  </p>
                </div>
              )}

              {!query && (
                <div className="px-6 py-14 text-center text-sm sm:px-14">
                  <MagnifyingGlassIcon className="mx-auto h-6 w-6 text-gray-400" />
                  <p className="mt-4 font-semibold text-gray-900 dark:text-gray-100">
                    Search documentation
                  </p>
                  <p className="mt-2 text-gray-500 dark:text-gray-400">
                    Find functions, classes, procedures, and guides.
                  </p>
                </div>
              )}

              <div className="flex flex-wrap items-center bg-gray-50 dark:bg-gray-700 px-4 py-2.5 text-xs text-gray-700 dark:text-gray-300">
                Type to search, press{' '}
                <kbd className="mx-1 flex h-5 w-5 items-center justify-center rounded border bg-white dark:bg-gray-600 font-semibold sm:mx-2">
                  ↑
                </kbd>
                <kbd className="mx-1 flex h-5 w-5 items-center justify-center rounded border bg-white dark:bg-gray-600 font-semibold sm:mx-2">
                  ↓
                </kbd>
                to navigate,{' '}
                <kbd className="mx-1 flex h-5 w-5 items-center justify-center rounded border bg-white dark:bg-gray-600 font-semibold sm:mx-2">
                  ↵
                </kbd>
                to select.
              </div>
            </Dialog.Panel>
          </Transition.Child>
        </div>
      </Dialog>
    </Transition.Root>
  );
}