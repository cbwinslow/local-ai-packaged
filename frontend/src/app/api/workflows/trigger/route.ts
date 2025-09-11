import { NextResponse } from 'next/server'
import { createRouteHandlerClient } from '@supabase/auth-helpers-nextjs'
import { cookies } from 'next/headers'

export async function POST(request: Request) {
  try {
    const { workflowId } = await request.json()
    
    // Verify user is authenticated
    const supabase = createRouteHandlerClient({ cookies })
    const { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      return new NextResponse(
        JSON.stringify({ error: 'Not authenticated' }),
        { status: 401, headers: { 'Content-Type': 'application/json' } }
      )
    }

    // In a real app, you would trigger the workflow here using n8n API or similar
    // For now, we'll simulate a successful response
    
    return NextResponse.json({
      success: true,
      workflowId,
      message: 'Workflow triggered successfully',
      timestamp: new Date().toISOString()
    })
    
  } catch (error) {
    console.error('Error triggering workflow:', error)
    return new NextResponse(
      JSON.stringify({ 
        error: 'Failed to trigger workflow',
        details: error instanceof Error ? error.message : 'Unknown error'
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    )
  }
}
