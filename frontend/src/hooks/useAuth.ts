import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Session } from '@supabase/supabase-js';
import { supabase } from '@/lib/supabase';

export const useAuth = (requireAuth = true) => {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const getSession = async () => {
      try {
        const { data: { session: currentSession }, error } = await supabase.auth.getSession();
        
        if (error) {
          console.error('Error getting session:', error);
          if (requireAuth) {
            router.push('/auth');
          }
          return;
        }

        setSession(currentSession);

        if (requireAuth && !currentSession) {
          router.push('/auth');
          return;
        }
      } catch (error) {
        console.error('Error in useAuth:', error);
        if (requireAuth) {
          router.push('/auth');
        }
      } finally {
        setLoading(false);
      }
    };

    getSession();

    // Set up auth state change listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setSession(session);
      
      if (requireAuth && !session) {
        router.push('/auth');
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, [requireAuth, router]);

  return { session, loading };
};

export default useAuth;
