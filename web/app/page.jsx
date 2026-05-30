/**
 * Casper Web - Main Page Component
 * Next.js page with React Query provider
 */

'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import CasperWeb from './CasperWeb';

// Create a client
const queryClient = new QueryClient();

export default function Home() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen">
        <CasperWeb />
      </div>
    </QueryClientProvider>
  );
}