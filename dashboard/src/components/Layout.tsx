import { useState } from 'react'
import Link from 'next/link'
import { useUser } from '@supabase/auth-helpers-react'
import { supabase } from '../lib/supabase'

interface NavigationItem {
  name: string
  href: string
  icon: string
}

const navigation: NavigationItem[] = [
  { name: 'Overview', href: '/', icon: '📊' },
  { name: 'Monitoring', href: '/monitoring', icon: '📈' },
  { name: 'Data Explorer', href: '/data-explorer', icon: '🔍' },
  { name: 'Configuration', href: '/config', icon: '⚙️' },
  { name: 'Troubleshooting', href: '/troubleshoot', icon: '🔧' },
  { name: 'Reports', href: '/reports', icon: '📊' },
  { name: 'Data', href: '/data', icon: '💾' },
  { name: 'Chatbot', href: '/chatbot', icon: '🤖' },
]

export function Layout({ children }: { children: React.ReactNode }) {
  const user = useUser()
  const [sidebarOpen, setSidebarOpen] = useState(false)

  const handleSignOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="flex h-full">
        {/* Mobile menu button */}
        <button
          className="md:hidden p-4"
          onClick={() => setSidebarOpen(!sidebarOpen)}
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        {/* Sidebar */}
        <div className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out bg-white shadow-lg md:relative md:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}>
          <div className="flex h-full flex-col">
            <div className="p-4 border-b">
              <div className="flex items-center">
                <div className="bg-indigo-600 text-white p-2 rounded-lg mr-3">
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">AI Platform Dashboard</h1>
                  <p className="text-sm text-gray-500">Monitor & Manage</p>
                </div>
              </div>
            </div>
            
            <nav className="flex-1 px-2 py-4 space-y-1">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-md hover:bg-gray-100 transition-colors group"
                  onClick={() => setSidebarOpen(false)}
                >
                  <span className="mr-3 text-lg">{item.icon}</span>
                  <span className="">{item.name}</span>
                </Link>
              ))}
            </nav>
            
            <div className="p-4 border-t bg-gray-50">
              {user ? (
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <span className="text-gray-600 font-medium text-sm">
                      {user.email?.[0].toUpperCase()}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {user.email}
                    </p>
                    <p className="text-xs text-gray-500 truncate">Admin</p>
                  </div>
                  <button
                    onClick={handleSignOut}
                    className="px-3 py-1 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <Link 
                  href="/auth" 
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 transition-colors"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>

        {/* Main content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
            <div className="p-4 md:p-6">
              {children}
            </div>
          </main>
        </div>

        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 z-40 bg-black bg-opacity-25 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </div>
    </div>
  )
}