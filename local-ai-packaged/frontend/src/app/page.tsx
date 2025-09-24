'use client'

import QueryForm from '@/components/QueryForm'
import { useAuth } from '@/hooks/useAuth'

export default function HomePage() {
  const { user, signIn, signUp, signOut } = useAuth()

  const handleSignIn = async () => {
    await signIn({ email: 'user@example.com', password: 'password' }) // Example; replace with form in prod
  }

  const handleSignUp = async () => {
    await signUp({ email: 'new@example.com', password: 'password' })
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900">
            Self-Hosted RAG Platform
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Query your knowledge graph with AI.
          </p>
        </div>
        {user ? (
          <div className="space-y-4">
            <p className="text-center text-sm text-gray-600">Welcome, {user.email}</p>
            <button
              onClick={signOut}
              className="group relative flex w-full justify-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600"
            >
              Sign out
            </button>
            <QueryForm />
          </div>
        ) : (
          <div className="space-y-4">
            <button
              onClick={handleSignIn}
              className="group relative flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >
              Sign in (Demo)
            </button>
            <button
              onClick={handleSignUp}
              className="group relative flex w-full justify-center rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
            >
              Sign up (Demo)
            </button>
            <p className="text-center text-xs text-gray-500">Demo credentials: Use any email/password for testing.</p>
          </div>
        )}
      </div>
    </main>
  )
}