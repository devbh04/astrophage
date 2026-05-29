import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Authentication redirects.
 * - Protected /(app)/* routes redirect to /login if no session cookie
 * - Auth /(auth)/* routes redirect to /chat if logged in
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("astrophage_session");

  const isAppRoute =
    pathname.startsWith("/chat") ||
    pathname.startsWith("/chart") ||
    pathname.startsWith("/family") ||
    pathname.startsWith("/calendar") ||
    pathname.startsWith("/settings");

  if (isAppRoute && !sessionCookie) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

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
