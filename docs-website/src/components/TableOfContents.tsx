import React, { useState, useEffect } from 'react';
import Link from 'next/link';

interface TocItem {
  id: string;
  title: string;
  level: number;
}

interface TableOfContentsProps {
  items: TocItem[];
}

export function TableOfContents({ items }: TableOfContentsProps) {
  const [activeId, setActiveId] = useState<string>('');

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveId(entry.target.id);
          }
        });
      },
      {
        rootMargin: '-20% 0% -35% 0%',
        threshold: 0,
      }
    );

    items.forEach(({ id }) => {
      const element = document.getElementById(id);
      if (element) {
        observer.observe(element);
      }
    });

    return () => {
      items.forEach(({ id }) => {
        const element = document.getElementById(id);
        if (element) {
          observer.unobserve(element);
        }
      });
    };
  }, [items]);

  if (!items.length) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 uppercase tracking-wide">
        On this page
      </h2>
      <nav className="space-y-1">
        {items.map((item) => (
          <Link
            key={item.id}
            href={`#${item.id}`}
            className={`block text-sm py-1 transition-colors ${
              item.level === 1 ? 'pl-0' : 
              item.level === 2 ? 'pl-4' : 
              item.level === 3 ? 'pl-8' : 'pl-12'
            } ${
              activeId === item.id
                ? 'text-blue-600 dark:text-blue-400 font-medium'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            {item.title}
          </Link>
        ))}
      </nav>
    </div>
  );
}