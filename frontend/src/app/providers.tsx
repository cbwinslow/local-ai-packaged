'use client'

import { createClient } from '@supabase/supabase-js'
import { SessionContextProvider } from '@supabase/auth-helpers-react'
import { useState } from 'react'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export default function Providers({ children }: { children: React.ReactNode }) {
  const [supabaseClient] = useState(() =>
    createClient(supabaseUrl, supabaseAnonKey)
  )

  return (
    <SessionContextProvider
      supabaseClient={supabaseClient}
      initialSession={null}
    >
      {children}
    </SessionContextProvider>
  )
}