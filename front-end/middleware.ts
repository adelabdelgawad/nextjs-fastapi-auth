import { NextResponse, type NextRequest } from "next/server";
import { getSession } from "@/lib/session";
import { routesConfig, publicPaths, AppRole } from "@/config/accessConfig";

type UserSession = {
  user: {
    email: string;
    roles: AppRole[];
  };
};

export async function middleware(request: NextRequest) {
  const { nextUrl, cookies } = request;
  const pathname = nextUrl.pathname;

  // Special handling for the /login route
  if (pathname === "/login") {
    const sessionToken = cookies.get("session")?.value;
    if (sessionToken) {
      const session = (await getSession()) as UserSession | null;
      if (session?.user) {
        console.log(`User ${session.user.email} already has a session, redirecting from login`);
        return redirectToHome(request);
      }
    }
  }

  // Allow public paths and static assets (excluding the special case above)
  if (
    publicPaths.includes(pathname) ||
    pathname.startsWith("/api") ||
    pathname.startsWith("/_next") ||
    pathname.match(/\.(png|jpg|jpeg|gif|ico)$/)
  ) {
    console.log("Inside public path check");
    return NextResponse.next();
  }

  // Check for existing session for non-public routes
  const sessionToken = cookies.get("session")?.value;
  const session = sessionToken ? (await getSession()) as UserSession | null : null;

  // Redirect to login if no valid session exists
  if (!session?.user) {
    console.log("No session found, redirecting to login");
    return redirectToLogin(request);
  }

  // Normalize user roles
  const userRoles = normalizeRoles(session.user.roles);

  // Check route access permissions
  const isAllowed = checkPathAccess(pathname, userRoles);
  if (!isAllowed) {
    console.warn(`Access denied for ${session.user.email} to ${pathname}`);
    return redirectToAccessDenied(request);
  }

  return NextResponse.next();
}

// Helper function to check path access
function checkPathAccess(path: string, userRoles: AppRole[]): boolean {
  const routeConfig = routesConfig.find(rc => rc.path === path);
  // Allow access if no specific config exists (public by default)
  if (!routeConfig) return true;
  return routeConfig.roles.some(role => userRoles.includes(role));
}

// Helper to normalize roles array
function normalizeRoles(roles: unknown): AppRole[] {
  if (!roles) return [];
  if (Array.isArray(roles)) {
    return roles.filter((r): r is AppRole => typeof r === "string" && isAppRole(r));
  }
  return typeof roles === "string" && isAppRole(roles) ? [roles] : [];
}

// Type guard for AppRole
function isAppRole(role: string): role is AppRole {
  return ["Admin", "User", "Ordertaker", "Manager"].includes(role);
}

// Redirection helpers
const redirectToLogin = (request: NextRequest) =>
  NextResponse.redirect(new URL("/login", request.url));

const redirectToHome = (request: NextRequest) =>
  NextResponse.redirect(new URL("/", request.url));

const redirectToAccessDenied = (request: NextRequest) =>
  NextResponse.redirect(new URL("/access-denied", request.url));

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
