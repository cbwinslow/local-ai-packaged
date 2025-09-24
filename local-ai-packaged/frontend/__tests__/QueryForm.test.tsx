import { render, screen, fireEvent } from '@testing-library/react';
import QueryForm from '../src/components/QueryForm';

// Mock fetch
global.fetch = jest.fn();

describe('QueryForm', () => {
  beforeEach(() => {
    (global.fetch as jest.Mock).mockClear();
  });

  it('renders QueryForm component', () => {
    render(<QueryForm />);
    expect(screen.getByRole('textbox', { name: /query/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
  });

  it('submits query and fetches from /query endpoint', async () => {
    const mockResponse = { response: 'test', sources: [] };
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    render(<QueryForm />);
    const input = screen.getByRole('textbox', { name: /query/i });
    const button = screen.getByRole('button', { name: /submit/i });

    fireEvent.change(input, { target: { value: 'test query' } });
    fireEvent.click(button);

    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: 'test query' }),
    });

    // Wait for async response if needed, but since no async update in test, just check call
  });
});