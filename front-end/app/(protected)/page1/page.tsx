// app/(protected)/page1/page.tsx
import React from 'react';
import { cookies } from 'next/headers'; // Import cookies function
import { redirect } from 'next/navigation'; // Import redirect function
import { UserPayload } from '@/types';

// Define fetch function outside component for clarity, or use a lib function
async function fetchPage1Data(token: string | undefined): Promise<UserPayload | null> {
    if (!token) return null;

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
        const response = await fetch(`${API_BASE_URL}/protected/page1`, {
            headers: {
                 // Forward the cookie from the incoming request
                'Cookie': `access_token=${token}`,
            },
            cache: 'no-store', // Ensure data isn't stale due to caching
        });

        if (!response.ok) {
            // Handle specific errors if needed (e.g., 401 vs 403)
            console.error(`SSR Page 1: Fetch failed with status ${response.status}`);
            return null; // Indicate failure
        }
        return await response.json() as UserPayload;
    } catch (error) {
        console.error('SSR Page 1: Fetch error:', error);
        return null; // Indicate failure
    }
}

// The Page component itself is async Server Component
export default async function Page1() {
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;

    const user = await fetchPage1Data(token);

    if (!user) {
        // If fetch failed (no token, invalid token, API error), redirect to login
        redirect('/login'); // Use the redirect function
    }

    // If fetch was successful, render the page with user data
    return (
        <div>
        <h1>Protected Page 1 (User/Admin Access)</h1>
        <p>Welcome, {user.fullname}!</p>
        <h2>Your Details (SSR):</h2>
        <ul>
            <li>Username: {user.username}</li>
            <li>Title: {user.title}</li>
            <li>Email: {user.email}</li>
            <li>Roles: {user.roles.join(', ')} {user.roles.includes(1) ? '(Admin)' : '(User)'}</li>
            <li>User ID: {user.userId}</li>
        </ul>
        </div>
    );
}