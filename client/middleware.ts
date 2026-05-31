import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Authentication redirects.
 *
 * The backend issues an HttpOnly session cookie on its own domain. In
 * cross-site production deployments (frontend on Vercel, backend on a
 * separate host) that cookie is NOT visible to the Next.js server, so
 * server-side redirects based on it always think the user is logged
 * out. To avoid the false redirect-to-login loop we delegate the auth
 * check to the (app) layout, which fires ``/auth/me`` from the browser
 * with credentials and bounces to ``/login`` itself on 401.
 *
 * What the middleware still does:
 *  - When the cookie IS visible (same-origin dev, or shared parent
 *    domain in prod), redirect ``/login`` and ``/register`` to ``/chat``
 *    so logged-in users don't see the auth screen flicker.
 *  - Otherwise pass through unchanged.
 */
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const sessionCookie = request.cookies.get("astrophage_session");

  const isAuthRoute =
    pathname.startsWith("/login") || pathname.startsWith("/register");

  if (isAuthRoute && sessionCookie) {
    return NextResponse.redirect(new URL("/chat", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/login", "/register"],
};
