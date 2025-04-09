// app/(protected)/admin/page2/page.tsx
import React from 'react';
import { cookies } from 'next/headers';
import { redirect } from 'next/navigation';
import { UserPayload } from '@/types'; // Adjust path

async function fetchPage2Data(token: string | undefined): Promise<{ user: UserPayload | null; status: number | null }> {
    if (!token) return { user: null, status: 401 }; // No token means unauthorized

    const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    try {
        const response = await fetch(`${API_BASE_URL}/protected/page2`, { // Call admin endpoint
            headers: {
                'Cookie': `access_token=${token}`,
            },
             cache: 'no-store',
        });

        if (!response.ok) {
            console.error(`SSR Admin Page 2: Fetch failed with status ${response.status}`);
            return { user: null, status: response.status }; // Return status code for handling
        }
        const user = await response.json() as UserPayload;
        return { user, status: response.status };
    } catch (error) {
        console.error('SSR Admin Page 2: Fetch error:', error);
        return { user: null, status: 500 }; // Indicate server/network error
    }
}

export default async function AdminPage2() {
    const cookieStore = await cookies();
    const token = cookieStore.get('access_token')?.value;

    const { user, status } = await fetchPage2Data(token);

    if (!user) {
        if (status === 403) {
             // Forbidden: User is authenticated but not an admin
             // Redirect to a non-admin page or show an access denied message here
             console.log('SSR Admin Page 2: Access forbidden (not admin), redirecting to /page1.');
             redirect('/page1');
        } else {
            // Unauthorized (401) or other fetch error, redirect to login
            console.log(`SSR Admin Page 2: Fetch status ${status}, redirecting to login.`);
            redirect('/login');
        }
    }

    // User is authenticated and authorized as admin
    return (
        <div>
            <h1>Protected Page 2 (ADMIN ONLY Access)</h1>
            <p>Welcome, Administrator {user.fullname}!</p>
            <p>This page is only visible to users with the admin role (SSR).</p>
            <pre style={{ background: '#f0f0f0', padding: '10px', borderRadius: '4px' }}>
                {JSON.stringify(user, null, 2)}
            </pre>
        </div>
    );
}