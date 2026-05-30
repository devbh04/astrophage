"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { authApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import Sidebar from "@/components/app-shell/Sidebar";
import Topbar from "@/components/app-shell/Topbar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const user = useAppStore((s) => s.user);
  const sidebarOpen = useAppStore((s) => s.sidebarOpen);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fire once on mount. Do NOT depend on router / setters from Zustand —
  // those are recreated each render and would loop the effect.
  useEffect(() => {
    let cancelled = false;
    authApi
      .me()
      .then((me) => {
        if (cancelled) return;
        useAppStore.getState().setUser(me);
        if (me.default_language) {
          useAppStore.getState().setLanguage(me.default_language);
        }
      })
      .catch((err) => {
        if (cancelled) return;
        const msg =
          err instanceof Error ? err.message : "Failed to verify session";
        // 401 → redirect to login. Anything else → show the error so we
        // don't leave the user staring at "Aligning the stars…" forever.
        if (/401|not authenticated|unauthor/i.test(msg)) {
          router.replace("/login");
        } else {
          setError(msg);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-3 h-3 rounded-full bg-solar-gold animate-pulse mx-auto mb-4" />
          <p className="font-annotation-sm text-solar-gold text-lg">
            Aligning the stars...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <p className="font-annotation-sm text-solar-gold text-xl mb-3">
            Couldn&apos;t reach the cosmos
          </p>
          <p className="font-body-md text-sm text-on-surface-variant mb-6">
            {error}
          </p>
          <p className="font-body-md text-xs text-outline-variant">
            Make sure the backend is running at{" "}
            <code className="font-mono">
              {process.env.NEXT_PUBLIC_API_URL || "http://localhost:7860"}
            </code>
            , then refresh the page.
          </p>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="h-[100dvh] bg-background flex overflow-hidden">
      <Sidebar />
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? "md:ml-72" : "md:ml-20"
        } pb-16 md:pb-0`}
      >
        <Topbar />
        <main className="flex-1 overflow-y-auto relative flex flex-col min-h-0">
          {children}
        </main>
      </div>
    </div>
  );
}
