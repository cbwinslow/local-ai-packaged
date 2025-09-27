import { createClient } from '@supabase/supabase-js';
import { NextApiRequest, NextApiResponse } from 'next';
import { getSession } from 'next-auth/react';

/**
 * Handle POST API requests to execute a SQL query via Supabase and return its result.
 *
 * Validates that the request is POST and that the caller is authenticated, expects a string
 * `query` in the request body, and requires NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_KEY
 * to be set. Executes the Supabase RPC `execute_sql` with `query_text`, records an audit log
 * entry for the execution, and responds with `columns` and `rows` from the RPC result.
 *
 * Responds with:
 * - 200 and { columns, rows } on success
 * - 400 and { error: 'Query is required' } when `query` is missing or not a string
 * - 401 and { error: 'Unauthorized' } when the request is unauthenticated
 * - 405 and { error: 'Method not allowed' } for non-POST requests
 * - 500 and an error payload for server configuration or execution failures (includes error details)
 */
export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const session = await getSession({ req });
  if (!session) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  const { query } = req.body;
  if (!query || typeof query !== 'string') {
    return res.status(400).json({ error: 'Query is required' });
  }

  // Initialize Supabase client
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseKey = process.env.SUPABASE_SERVICE_KEY;
  
  if (!supabaseUrl || !supabaseKey) {
    return res.status(500).json({ error: 'Server configuration error' });
  }

  const supabase = createClient(supabaseUrl, supabaseKey);

  try {
    // Execute the query
    const { data, error } = await supabase.rpc('execute_sql', {
      query_text: query,
    });

    if (error) throw error;

    // Log the query in audit logs
    await supabase.from('audit_logs').insert({
      action: 'query_execute',
      resource_type: 'sql_query',
      metadata: { 
        query,
        result_count: data?.length || 0,
      },
      user_id: session.user?.id,
    });

    return res.status(200).json({
      columns: data?.columns || [],
      rows: data?.rows || [],
    });
  } catch (error) {
    console.error('Query execution error:', error);
    return res.status(500).json({ 
      error: 'Error executing query',
      details: error.message,
    });
  }
}
