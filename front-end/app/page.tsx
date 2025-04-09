// app/page.tsx
import Link from 'next/link';
import React from 'react';

export default function HomePage() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>Welcome!</h1>
      <p>This is the public landing page.</p>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        <li style={{ marginBottom: '10px' }}>
          <Link href="/login" style={{ textDecoration: 'none', color: '#0070f3' }}>Login</Link> to access protected areas.
        </li>
        <li style={{ marginBottom: '10px' }}>
          <Link href="/page1" style={{ textDecoration: 'none', color: '#0070f3' }}>Try accessing Page 1</Link> (will redirect if not logged in)
        </li>
        <li>
          <Link href="/admin/page2" style={{ textDecoration: 'none', color: '#0070f3' }}>Try accessing Admin Page 2</Link> (will redirect if not admin/logged in)
        </li>
      </ul>
    </div>
  );
}