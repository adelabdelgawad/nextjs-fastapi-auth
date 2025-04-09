// app/(auth)/login/page.tsx
"use client"; // Mark as a Client Component

import React, { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation'; // Use navigation hook from next/navigation
import api from '@/lib/api'; // Adjust path based on actual structure

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Call the FastAPI backend login endpoint
      await api.post('/login', { username });
      // Login successful, cookie is set by FastAPI via Set-Cookie header
      // Redirect to a protected page using App Router's router
      router.push('/page1'); // Navigate to the protected page
      router.refresh(); // Optional: Force refresh to ensure layout/server components re-evaluate if needed
    } catch (err: any) {
      console.error('Login failed:', err);
      const errorMsg = err.response?.data?.detail || 'Login failed. Please try again.';
      setError(errorMsg);
    } finally {
       setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '400px', margin: '50px auto', padding: '20px', border: '1px solid #ccc' }}>
      <h1>Login</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '15px' }}>
          <label htmlFor="username" style={{ display: 'block', marginBottom: '5px' }}>Username:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            placeholder="Try 'admin_user' or 'regular_user'"
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>
        {error && <p style={{ color: 'red', marginBottom: '15px' }}>{error}</p>}
        <button
          type="submit"
          disabled={loading}
          style={{ width: '100%', padding: '10px', background: '#0070f3', color: 'white', border: 'none', cursor: 'pointer' }}
        >
          {loading ? 'Logging in...' : 'Login'}
        </button>
      </form>
    </div>
  );
}