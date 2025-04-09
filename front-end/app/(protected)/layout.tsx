// app/(protected)/layout.tsx
"use client"; // Needs to be client for hook and button interactivity

import React from 'react';
import Link from 'next/link';
import { LogoutButton } from '@/components/logout-button';
import {useTokenRefresh} from '@/hooks/useTokenRefresh';

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Run the token refresh hook for all pages within this layout
  useTokenRefresh();

  return (
    <div>
      <nav style={{ background: '#eee', padding: '10px 15px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Link href="/page1" style={{ marginRight: '15px', textDecoration: 'none', color: '#333' }}>Page 1 (User)</Link>
          <Link href="/admin/page2" style={{ marginRight: '15px', textDecoration: 'none', color: '#333' }}>Page 2 (Admin)</Link>
        </div>
        <LogoutButton />
      </nav>
      <main style={{ padding: '20px' }}>
        {children}
      </main>
    </div>
  );
}