"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

function hasSessionCookie(): boolean {
  if (typeof document === "undefined") return false;
  return document.cookie
    .split(";")
    .some((c) => c.trim().startsWith("astrophage_session="));
}

export default function HeroSection() {
  const [isAuthed, setIsAuthed] = useState(false);

  useEffect(() => {
    setIsAuthed(hasSessionCookie());
  }, []);

  const primaryHref = isAuthed ? "/chat" : "/register";
  const primaryLabel = isAuthed ? "OPEN ASTROPHAGE" : "GENERATE YOUR BIRTH CHART";
  const secondaryHref = isAuthed ? "/chart" : "/login";
  const secondaryLabel = isAuthed ? "VIEW MY CHART" : "SIGN IN";

  return (
    <section className="relative min-h-[90vh] flex items-center px-margin-mobile md:px-margin-desktop overflow-hidden max-w-[1440px] mx-auto mt-24">
      <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter w-full">
        <div className="col-span-4 md:col-start-2 md:col-span-10 relative z-20 mt-12 md:mt-0 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 wobbly-border-sm border border-outline/30 bg-surface-container mb-8">
            <span className="w-2 h-2 rounded-full bg-solar-gold animate-pulse"></span>
            <span className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.15em]">
              SYSTEM ONLINE // ALIGNMENT: NOMINAL
            </span>
          </div>
          <h1 className="font-display-lg text-display-lg-mobile md:text-display-lg text-primary mb-6">
            Decode Your <span className="font-annotation-sm text-6xl md:text-8xl text-solar-gold -ml-4">Destiny</span>
            <br />
            In The Cosmic Radiance
          </h1>
          <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl mx-auto mb-10">
            Hyper-personalized AI Vedic Astrology engineered with quantum precision and the heart of a spiritual elder. Initiate your sequence.
          </p>
          <div className="flex flex-col items-center gap-4 relative">
            <div className="flex flex-col sm:flex-row justify-center items-center gap-4 relative flex-wrap w-full">
              <div className="absolute -left-12 top-1/2 -translate-y-1/2 hidden xl:block opacity-50">
                <svg fill="none" height="40" viewBox="0 0 40 40" width="40" xmlns="http://www.w3.org/2000/svg">
                  <path
                    d="M35 20L5 20M35 20L25 10M35 20L25 30"
                    stroke="#1c1b1b"
                    strokeDasharray="4 4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                  ></path>
                </svg>
              </div>
              <Link
                href={primaryHref}
                className="btn-primary wobbly-border font-nav-label text-nav-label px-8 py-4 flex items-center justify-center gap-3 uppercase tracking-[0.15em]"
              >
                {primaryLabel}
                <span className="material-symbols-outlined">rocket_launch</span>
              </Link>
              <a
                href="https://youtu.be/6qW0K6iMzTg"
                target="_blank"
                rel="noopener noreferrer"
                id="hero-watch-demo-button"
                className="group relative wobbly-border font-nav-label text-nav-label px-8 py-4 flex items-center justify-center gap-3 uppercase tracking-[0.15em] bg-surface-container-lowest text-primary border-2 border-solar-gold shadow-[4px_4px_0px_0px_#D4AF37] hover:shadow-[6px_6px_0px_0px_#D4AF37] hover:-translate-x-0.5 hover:-translate-y-0.5 active:translate-x-1 active:translate-y-1 active:shadow-none hover:bg-solar-gold/10 transition-all duration-300"
              >
                <span className="relative flex h-2.5 w-2.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-solar-gold opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-solar-gold"></span>
                </span>
                <span>WATCH VIDEO DEMO HERE</span>
                <span className="material-symbols-outlined text-solar-gold text-xl transition-transform duration-300 group-hover:scale-125">
                  play_circle
                </span>
              </a>
              <Link
                href={secondaryHref}
                className="btn-ghost wobbly-border font-nav-label text-nav-label px-8 py-4 flex items-center justify-center gap-3 uppercase tracking-[0.15em] hover:translate-x-1 hover:translate-y-1"
              >
                {secondaryLabel}
                <span className="material-symbols-outlined">
                  {isAuthed ? "stars" : "login"}
                </span>
              </Link>
            </div>
            <div className="font-annotation-sm text-base md:text-lg text-solar-gold flex items-center gap-2 mt-1">
              <span>✦</span>
              <span>Watch full platform walkthrough &amp; AI consultation in action</span>
              <span>↗</span>
            </div>
          </div>
        </div>
        <div className="col-span-4 md:col-start-3 md:col-span-8 mt-48 relative group">
          <div className="tape-strip"></div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt="Golden Vedic Chart"
            className="w-full object-cover grayscale-transition wobbly-border shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)]"
            src="/golden_vedic_chart.png"
          />
          <a
            href="https://youtu.be/6qW0K6iMzTg"
            target="_blank"
            rel="noopener noreferrer"
            className="absolute bottom-6 left-6 md:bottom-8 md:left-8 z-20 flex items-center gap-3 px-5 py-3 bg-surface-container-lowest/95 backdrop-blur-md wobbly-border-sm border border-solar-gold shadow-[4px_4px_0px_0px_#D4AF37] hover:shadow-[6px_6px_0px_0px_#D4AF37] hover:-translate-y-0.5 transition-all duration-300 text-primary group"
          >
            <span className="w-9 h-9 rounded-full bg-solar-gold flex items-center justify-center text-surface-container-lowest group-hover:scale-110 transition-transform">
              <span className="material-symbols-outlined text-xl">play_arrow</span>
            </span>
            <div className="text-left">
              <p className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">Live Walkthrough</p>
              <p className="font-annotation-sm text-base text-primary font-bold">Watch Video Demo Here ↗</p>
            </div>
          </a>
          <div className="absolute -right-8 top-1/2 -translate-y-1/2 vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
            EDITORIAL // 01
          </div>
        </div>
      </div>
    </section>
  );
}
