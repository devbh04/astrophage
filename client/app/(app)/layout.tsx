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
  const { user, setUser, setLanguage, sidebarOpen } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    authApi
      .me()
      .then((me) => {
        setUser(me);
        if (me.default_language) setLanguage(me.default_language);
      })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, [router, setUser, setLanguage]);

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

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background flex">
      <Sidebar />
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? "md:ml-72" : "md:ml-20"
        } pb-16 md:pb-0`}
      >
        <Topbar />
        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
