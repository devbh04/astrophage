import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Middleware for authentication redirects.
 *
 * - Protected routes (/(app)/*): redirect to /login if no session cookie
 * - Auth routes (/(auth)/*): redirect to /chat if session cookie exists
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("astrophage_session");

  // Protected app routes — require auth
  const isAppRoute =
    pathname.startsWith("/chat") ||
    pathname.startsWith("/chart") ||
    pathname.startsWith("/family") ||
    pathname.startsWith("/calendar") ||
    pathname.startsWith("/settings");

  if (isAppRoute && !sessionCookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  // Auth routes — redirect to app if already logged in
  const isAuthRoute =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  if (isAuthRoute && sessionCookie) {
    return NextResponse.redirect(new URL("/chat", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/chat/:path*",
    "/chart/:path*",
    "/family/:path*",
    "/calendar/:path*",
    "/settings/:path*",
    "/login",
    "/register",
  ],
};
