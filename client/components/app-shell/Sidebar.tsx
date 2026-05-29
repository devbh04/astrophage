"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageCircle,
  BarChart3,
  Users,
  Calendar,
  Settings,
  PanelLeftClose,
  PanelLeft,
} from "lucide-react";
import { useAppStore } from "@/lib/store";

const NAV_ITEMS = [
  { href: "/chat", label: "CHAT", icon: MessageCircle },
  { href: "/chart", label: "CHART", icon: BarChart3 },
  { href: "/family", label: "FAMILY", icon: Users },
  { href: "/calendar", label: "CALENDAR", icon: Calendar },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, sidebarOpen, toggleSidebar } = useAppStore();

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`fixed left-0 top-0 h-full z-40 hidden md:flex flex-col
          border-r border-dashed border-outline/20
          bg-surface-container-lowest/95 backdrop-blur-md
          transition-all duration-300 ease-in-out
          ${sidebarOpen ? "w-72" : "w-20"}`}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-dashed border-outline/20">
          {sidebarOpen && (
            <Link href="/" className="font-annotation-sm text-xl text-primary tracking-tight">
              ASTROPHAGE
            </Link>
          )}
          <button
            onClick={toggleSidebar}
            className="p-2 hover:bg-surface-container rounded-md transition-colors text-on-surface-variant hover:text-primary"
          >
            {sidebarOpen ? (
              <PanelLeftClose size={18} />
            ) : (
              <PanelLeft size={18} />
            )}
          </button>
        </div>

        {/* User profile card */}
        {user && sidebarOpen && (
          <div className="p-4 mx-4 mt-4 glass-panel wobbly-border-sm">
            <p className="font-headline-md text-sm text-primary truncate">
              {user.name}
            </p>
            <p className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant mt-1">
              {user.email}
            </p>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200
                  font-nav-label text-nav-label uppercase tracking-[0.15em]
                  ${
                    isActive
                      ? "bg-surface-container text-primary border-l-2 border-solar-gold"
                      : "text-on-surface-variant hover:bg-surface-container/50 hover:text-primary"
                  }
                  ${!sidebarOpen ? "justify-center px-2" : ""}`}
              >
                <Icon
                  size={18}
                  className={isActive ? "text-solar-gold" : ""}
                />
                {sidebarOpen && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="p-4 border-t border-dashed border-outline/20">
          <Link
            href="/settings"
            className={`flex items-center gap-3 px-4 py-3 rounded-md transition-all duration-200
              font-nav-label text-nav-label uppercase tracking-[0.15em]
              text-on-surface-variant hover:bg-surface-container/50 hover:text-primary
              ${pathname === "/settings" ? "bg-surface-container text-primary" : ""}
              ${!sidebarOpen ? "justify-center px-2" : ""}`}
          >
            <Settings size={18} />
            {sidebarOpen && <span>SETTINGS</span>}
          </Link>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 md:hidden bg-surface-container-lowest/95 backdrop-blur-md border-t border-dashed border-outline/20">
        <div className="flex justify-around py-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname.startsWith(item.href);
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center gap-1 px-3 py-2 rounded-md transition-colors
                  ${isActive ? "text-solar-gold" : "text-on-surface-variant"}`}
              >
                <Icon size={20} />
                <span className="font-nav-label text-[9px] uppercase tracking-wider">
                  {item.label}
                </span>
              </Link>
            );
          })}
          <Link
            href="/settings"
            className={`flex flex-col items-center gap-1 px-3 py-2 rounded-md transition-colors
              ${pathname === "/settings" ? "text-solar-gold" : "text-on-surface-variant"}`}
          >
            <Settings size={20} />
            <span className="font-nav-label text-[9px] uppercase tracking-wider">
              SETTINGS
            </span>
          </Link>
        </div>
      </nav>
    </>
  );
}
