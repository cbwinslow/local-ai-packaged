import { NextPage } from 'next';
import { MonitoringDashboard } from '@/components/MonitoringDashboard';
import { Layout } from '@/components/Layout';
import { useSession } from 'next-auth/react';
import { useRouter } from 'next/router';
import { useEffect } from 'react';

const MonitoringPage: NextPage = () => {
  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth');
    }
  }, [status, router]);

  if (status === 'loading') {
    return (
      <Layout>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </Layout>
    );
  }

  if (!session) {
    return null; // Will be redirected by the effect
  }

  return (
    <Layout>
      <div className="container mx-auto px-4 py-8">
        <MonitoringDashboard />
      </div>
    </Layout>
  );
};

export default MonitoringPage;
