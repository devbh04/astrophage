"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

function hasSessionCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .some((c) => c.trim().startsWith("astrophage_session="));
}

export default function Navbar() {
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    setIsAuthed(hasSessionCookie());
  }, []);

  const ctaHref = isAuthed ? "/chat" : "/login";
  const ctaLabel = isAuthed ? "Open Astrophage" : "Decode Destiny";

  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-margin-mobile md:px-margin-desktop py-6 max-w-full border-b border-dashed border-outline/20 bg-background/80 backdrop-blur-md">
      <Link
        href="/"
        className="font-annotation-sm text-display-lg-mobile md:text-headline-md tracking-tighter text-primary"
      >
        ASTROPHAGE
      </Link>

      <div className="hidden md:flex space-x-8">
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="/chart"
        >
          Chart
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="/calendar"
        >
          Calendar
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="/family"
        >
          Family
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="/chat"
        >
          Chat
        </Link>
      </div>

      <Link
        href={ctaHref}
        className="hidden md:flex font-nav-label text-nav-label uppercase tracking-[0.15em] px-6 py-2 border border-primary wobbly-border-sm items-center gap-2 hover:bg-secondary-container/10 hover:text-primary transition-all duration-300 hover:translate-x-1 hover:translate-y-1"
      >
        <span className="material-symbols-outlined" style={{ fontSize: "16px" }}>
          {isAuthed ? "auto_awesome" : "explore"}
        </span>
        {ctaLabel}
      </Link>

      <Link href={ctaHref} className="md:hidden text-primary">
        <span className="material-symbols-outlined">menu</span>
      </Link>
    </nav>
  );
}
