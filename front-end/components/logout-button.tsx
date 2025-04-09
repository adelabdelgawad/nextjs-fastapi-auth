// components/LogoutButton.tsx
"use client";

import React from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api'; // Adjust path

export function LogoutButton() {
    const router = useRouter();

    const handleLogout = async () => {
        try {
            await api.post('/logout'); // Ask backend to clear the cookie
        } catch (error) {
            console.error('Logout API call failed:', error);
            // Proceed with client-side redirect even if backend call fails
        } finally {
             // Redirect to login regardless of API call success/failure
            router.push('/login');
            router.refresh(); // Force re-render to clear any stale server component data
        }
    };

    return (
        <button onClick={handleLogout} style={{ background: 'crimson', color: 'white', border: 'none', padding: '8px 15px', cursor: 'pointer', borderRadius: '4px' }}>
            Logout
        </button>
    );
}