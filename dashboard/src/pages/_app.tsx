import type { AppProps } from 'next/app'
import { useState } from 'react'
import { SessionContextProvider } from '@supabase/auth-helpers-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { supabase } from '../lib/supabase'
import '../styles/globals.css'
import { Layout } from '../components/Layout'

/**
 * Application root that initializes global providers and renders the active page inside the app layout.
 *
 * Initializes a React Query client with a 5-minute query stale time and one retry, provides Supabase
 * session context using the provided supabase client and initial session from pageProps, and wraps
 * the active page Component in the shared Layout.
 *
 * @returns The root JSX element providing Supabase session and React Query contexts and rendering the page within the Layout.
 */
export default function App({
  Component,
  pageProps,
}: AppProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5 minutes
        retry: 1,
      },
    },
  }))

  return (
    <SessionContextProvider
      supabaseClient={supabase}
      initialSession={pageProps.initialSession}
    >
      <QueryClientProvider client={queryClient}>
        <Layout>
          <Component {...pageProps} />
        </Layout>
      </QueryClientProvider>
    </SessionContextProvider>
  )
}