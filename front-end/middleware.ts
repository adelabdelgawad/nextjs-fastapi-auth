// middleware.ts (at the root level, alongside `app`)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value;
  const { pathname } = request.nextUrl;

  // Define protected paths
  const protectedPaths = ['/page1', '/admin/page2']; // Add any other base protected paths

  // Check if the current path starts with any of the protected paths
  const isAccessingProtected = protectedPaths.some(path => pathname.startsWith(path));

  // If accessing a protected path without a token, redirect to login
  if (isAccessingProtected && !token) {
    console.log(`Middleware: No token found for protected route ${pathname}. Redirecting to login.`);
    const loginUrl = new URL('/login', request.url); // Construct absolute URL for redirection
    return NextResponse.redirect(loginUrl);
  }

  // If accessing login page *with* a token, redirect to a default protected page (e.g., page1)
  if (pathname === '/login' && token) {
     console.log('Middleware: User already logged in, redirecting from /login to /page1.');
     const page1Url = new URL('/page1', request.url);
     return NextResponse.redirect(page1Url);
  }

  // Allow the request to proceed
  return NextResponse.next();
}

// Configure the middleware to run only on specific paths
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
    // Apply specifically to login and protected paths if preferred:
    // '/login',
    // '/page1/:path*',
    // '/admin/:path*',
  ],
};