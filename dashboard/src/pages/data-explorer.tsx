import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/router';
import { Box, Button, Card, Container, Grid, Paper, TextField, Typography } from '@mui/material';
import { DataGrid, GridColDef } from '@mui/x-data-grid';
import { styled } from '@mui/material/styles';
import dynamic from 'next/dynamic';

// Dynamically import the SQL editor with no SSR
const CodeEditor = dynamic(
  () => import('@uiw/react-textarea-code-editor').then((mod) => mod.default),
  { ssr: false }
);

const Item = styled(Paper)(({ theme }) => ({
  backgroundColor: theme.palette.mode === 'dark' ? '#1A2027' : '#fff',
  ...theme.typography.body2,
  padding: theme.spacing(2),
  color: theme.palette.text.secondary,
  height: '100%',
  display: 'flex',
  flexDirection: 'column',
}));

interface QueryResult {
  columns: { name: string; type: string }[];
  rows: any[];
  error?: string;
}

export default function DataExplorer() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [query, setQuery] = useState('SELECT * FROM documents LIMIT 10');
  const [results, setResults] = useState<QueryResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin');
    }
  }, [status, router]);

  const executeQuery = async () => {
    if (!query.trim()) {
      setError('Please enter a SQL query');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.accessToken}`,
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Error executing query');
      }

      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
      console.error('Query execution error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const columns: GridColDef[] = results?.columns.map(col => ({
    field: col.name,
    headerName: col.name,
    flex: 1,
    valueFormatter: (params) => {
      if (params.value === null || params.value === undefined) return 'NULL';
      if (typeof params.value === 'object') return JSON.stringify(params.value);
      return String(params.value);
    },
  })) || [];

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Data Explorer
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Item>
            <Typography variant="h6" gutterBottom>
              SQL Query
            </Typography>
            <Box sx={{ mb: 2 }}>
              <CodeEditor
                value={query}
                language="sql"
                placeholder="Enter your SQL query here"
                onChange={(evn) => setQuery(evn.target.value)}
                padding={15}
                style={{
                  fontSize: '0.875rem',
                  backgroundColor: '#f5f5f5',
                  fontFamily: '"Fira code", "Fira Mono", monospace',
                  minHeight: '150px',
                  borderRadius: '4px',
                }}
              />
            </Box>
            <Button
              variant="contained"
              color="primary"
              onClick={executeQuery}
              disabled={isLoading}
            >
              {isLoading ? 'Executing...' : 'Execute Query'}
            </Button>
          </Item>
        </Grid>

        <Grid item xs={12}>
          <Item>
            <Typography variant="h6" gutterBottom>
              Results
            </Typography>
            {error && (
              <Typography color="error" sx={{ mb: 2 }}>
                Error: {error}
              </Typography>
            )}
            {results ? (
              <Box sx={{ height: 500, width: '100%' }}>
                <DataGrid
                  rows={results.rows}
                  columns={columns}
                  pageSize={10}
                  rowsPerPageOptions={[10, 25, 50]}
                  disableSelectionOnClick
                  getRowId={(row) => row.id || Math.random()}
                />
              </Box>
            ) : (
              <Typography>No results to display. Run a query to see results.</Typography>
            )}
          </Item>
        </Grid>
      </Grid>
    </Container>
  );
}
