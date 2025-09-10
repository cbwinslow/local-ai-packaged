import type { AppProps } from 'next/app'
import { useState } from 'react'
import { SessionContextProvider } from '@supabase/auth-helpers-react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { supabase } from '../lib/supabase'
import '../styles/globals.css'
import { Layout } from '../components/Layout'

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