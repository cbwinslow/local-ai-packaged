import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../src/hooks/useAuth';
import { createClient } from '@supabase/supabase-js';

// Mock Supabase createClient
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(),
}));

describe('useAuth hook', () => {
  it('should sign in with credentials', async () => {
    const mockSupabase = {
      auth: {
        signInWithPassword: jest.fn().mockResolvedValue({ data: { user: { id: '1' } }, error: null }),
      },
    };
    (createClient as jest.Mock).mockReturnValue(mockSupabase);

    const { result } = renderHook(() => useAuth());

    await act(async () => {
      await result.current.signIn('user@example.com', 'password');
    });

    expect(mockSupabase.auth.signInWithPassword).toHaveBeenCalledWith({
      email: 'user@example.com',
      password: 'password',
    });
  });
});