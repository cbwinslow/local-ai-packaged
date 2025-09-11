'use client'

import React from 'react'
import { SessionContextProvider } from '@supabase/auth-helpers-react'
import { supabase } from '@/lib/supabase'

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <SessionContextProvider
      supabaseClient={supabase}
      initialSession={null}
    >
      {children}
    </SessionContextProvider>
  )
}