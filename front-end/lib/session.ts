"use server";

import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { JWTPayload } from "jose";

const NEXT_PUBLIC_FASTAPI_URL = process.env.NEXT_PUBLIC_FASTAPI_URL;

// Ensure the SESSION_SECRET environment variable is defined
const secretKey = process.env.SESSION_SECRET;
if (!secretKey) {
  throw new Error("SESSION_SECRET environment variable is not defined");
}
const encodedKey = new TextEncoder().encode(secretKey);

export async function encrypt(payload: JWTPayload) {
  return new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("7d")
    .sign(encodedKey);
}

export async function decrypt(session = "") {
  try {
    const { payload } = await jwtVerify(session, encodedKey, {
      algorithms: ["HS256"],
    });
    return payload;
  } catch (error) {
    console.error("Failed to verify session:", error);
    return null;
  }
}

export async function createSession(user: string) {
  const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
  const session = await encrypt({ user, expiresAt });
  const cookieStore = await cookies();

  cookieStore.set("session", session, {
    httpOnly: true,
    secure: true,
    expires: expiresAt,
    sameSite: "lax", // Ensure consistency across all functions
    path: "/",
  });
}

export async function updateSession() {
  const cookieStore = await cookies();
  const session = cookieStore.get("session")?.value;
  const payload = await decrypt(session);

  if (!session || !payload) {
    return null;
  }

  const expires = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);

  cookieStore.set("session", session, {
    httpOnly: true,
    secure: true,
    expires: expires,
    sameSite: "lax", // Ensure consistency across all functions
    path: "/",
  });
}

export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete('session')
}

export async function login(formData: FormData) {
  const username = formData.get("username") as string;
  const password = formData.get("password") as string;

  try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_FASTAPI_URL}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      let errorMessage = "Authentication failed";
      switch (response.status) {
        case 401:
          errorMessage = "Invalid Username or Password";
          break;
        case 500:
          errorMessage = "Internal Server Error";
          break;
        case 503:
          errorMessage = "Network Connection Error";
          break;
      }
      return { errors: { general: errorMessage } };
    }

    // Parse user data and store session
    const user = await response.json();
    await createSession(user);

    return { success: true };
  } catch (error) {
    console.error("Error logging in:", error);
    return {
      errors: {
        general: "Unable to connect to the server. Please try again later.",
      },
    };
  }
}
export async function getSession() {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get('session')?.value;
  if (!sessionCookie) return null;
  const payload = await decrypt(sessionCookie);
  if (payload) {
    return payload; // Ensure this returns an object with a 'token' property
  }
  return null;
}




export async function logout() {
  deleteSession()
  redirect('/login')
}