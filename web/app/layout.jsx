/**
 * Casper Web - Layout Component
 * Next.js root layout
 */

import './globals.css';

export const metadata = {
  title: 'Casper Node - AI Orchestration Platform',
  description: 'Mobile-first orchestration toolkit for Termux-driven workflows, remote AI agents, and GitHub CI/CD deployment',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}