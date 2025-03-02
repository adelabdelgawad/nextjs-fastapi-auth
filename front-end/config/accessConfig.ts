// Define valid application roles as a type
export type AppRole = "Admin" | "User";

// Define route configuration structure
export interface RouteConfig {
  path: string;
  roles: AppRole[];
  navSection?: string;
  navTitle?: string;
  navDescription?: string;
}

// Centralized route configuration
export const routesConfig: RouteConfig[] = [
  {
    path: "/request/new-request",
    roles: ["Admin", "User"],
    navSection: "Request",
    navTitle: "New Request",
    navDescription: "Create a new meal request.",
  },
];

// Publicly accessible paths
export const publicPaths = [
  "/access-denied",
  "/login",
];