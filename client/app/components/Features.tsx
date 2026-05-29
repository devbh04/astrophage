export default function Features() {
  return (
    <>
      {/* 3. MULTILINGUAL SOUL CONNECTION */}
      <section className="py-32 px-margin-mobile md:px-margin-desktop relative z-10 border-t border-dashed border-outline/20">
        <div className="max-w-[1440px] mx-auto">
          <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter items-center">
            <div className="col-span-4 md:col-start-2 md:col-span-4 relative fade-in-up">
              <div className="absolute -left-8 top-0 bottom-0 flex items-center justify-center">
                <div className="vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
                  EDITORIAL // 03
                </div>
              </div>
              <h2 className="font-headline-md text-headline-md text-primary mb-4">
                Soul Connection<br />
                <span className="font-annotation-sm text-5xl text-solar-gold block mt-2">in your native tongue</span>
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant mb-6 mt-6">
                Astrophage transcends binary code. It speaks the language of your ancestors. Whether it&apos;s the poetic
                resonance of Hindi, the deep roots of Marathi, or the ancient wisdom of Tamil, our AI articulates cosmic
                truths with cultural warmth and elder-like reverence.
              </p>
              <div className="flex flex-wrap gap-3 mt-8">
                <span className="px-4 py-2 wobbly-border-sm border border-outline/30 text-xs font-nav-label text-on-surface tracking-widest bg-surface-container">HINDI</span>
                <span className="px-4 py-2 wobbly-border-sm border border-outline/30 text-xs font-nav-label text-on-surface tracking-widest bg-surface-container">MARATHI</span>
                <span className="px-4 py-2 wobbly-border-sm border border-outline/30 text-xs font-nav-label text-on-surface tracking-widest bg-surface-container">TAMIL</span>
                <span className="px-4 py-2 wobbly-border-sm border border-outline/30 text-xs font-nav-label text-outline-variant tracking-widest">+12 MORE</span>
              </div>
            </div>
            <div className="col-span-4 md:col-start-7 md:col-span-5 relative mt-12 md:mt-0 fade-in-up" style={{ transitionDelay: '100ms' }}>
              <div className="tape-strip-right"></div>
              <div className="relative h-[400px] wobbly-border glass-panel flex items-center justify-center p-8 bg-surface-container-low shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)]">
                <div className="text-center z-10">
                  <span className="material-symbols-outlined text-6xl text-on-surface mb-4">translate</span>
                  <div className="font-annotation-sm text-xl text-solar-gold mt-4">Translating cosmic signals...</div>
                  <div className="mt-8 space-y-3 opacity-30">
                    <div className="h-[1px] w-48 border-b border-dashed border-primary mx-auto"></div>
                    <div className="h-[1px] w-32 border-b border-dashed border-primary mx-auto"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 4. DASHA TIMELINES & LUNAR CYCLES */}
      <section className="py-32 px-margin-mobile md:px-margin-desktop relative z-10 border-t border-dashed border-outline/20">
        <div className="max-w-[1440px] mx-auto">
          <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter items-center">
            <div className="col-span-4 md:col-start-6 md:col-span-6 relative group fade-in-up order-2 mt-12 md:mt-0">
              <div className="tape-strip"></div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Lunar Phases"
                className="relative wobbly-border object-cover shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)] z-10 grayscale-transition"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuC4Qj-6RscG2TbOiPUnZc6HI0KwHGwaZYkT_SOGeqFfDbK7WvAdTPrgMZvbe65yDntFbSFVkbBjFA65cIz4EMzysunx4Ffso3ih3Orj7PS9PtCQLPtYckyy2DtlCD4EQa8XbeJKfY5xQw3bVwJzMr5gO2xBMoY14f6SDOSdWEfmfeTo34HRFK9XkpTh7sXCfeb6ikQNFDNpV8M8ORw2E_WNQCYsZbkXC39N9F5Z-byJ_szcfMjqEO_vlRaXHmj1xuGNJ-6eP4KQUno"
              />
              <div className="absolute -right-10 top-1/2 -translate-y-1/2 vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
                EDITORIAL // 04
              </div>
            </div>
            <div className="col-span-4 md:col-start-2 md:col-span-4 relative order-1 fade-in-up">
              <h2 className="font-headline-md text-headline-md text-primary mb-4">
                Dasha Timelines &amp;<br />
                <span className="font-annotation-sm text-5xl text-solar-gold block mt-2">Lunar Cycles</span>
              </h2>
              <p className="font-body-md text-body-md text-on-surface-variant mb-6 mt-6">
                Map your soul&apos;s journey across the expansive Dasha periods. Our quantum algorithms synchronize intimately
                with the lunar nodes, providing precise timing for your karmic chapters. Understand the exact phases of
                your personal evolution.
              </p>
              <button className="mt-4 w-fit px-8 py-3 border border-primary wobbly-border-sm text-primary font-nav-label text-xs uppercase tracking-widest hover:bg-secondary-container/10 hover:translate-x-1 hover:translate-y-1 transition-all">
                TRACE YOUR CYCLE
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* 5. VEDIC ACCURACY & PLANETARY ALIGNMENT */}
      <section className="py-32 px-margin-mobile md:px-margin-desktop relative z-10 border-t border-dashed border-outline/20">
        <div className="max-w-[1440px] mx-auto">
          <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter items-center">
            <div className="col-span-4 md:col-start-2 md:col-span-10 text-center mb-16 fade-in-up">
              <h2 className="font-headline-md text-headline-md text-primary">
                Vedic Accuracy &amp; <span className="font-annotation-sm text-5xl text-solar-gold">Planetary</span> Alignment
              </h2>
              <p className="font-nav-label text-nav-label text-on-surface-variant mt-4 tracking-[0.2em] uppercase">
                ANALYZING SATURNIAN TRANSITS &amp; NAKSHATRAS
              </p>
            </div>
            <div className="col-span-4 md:col-start-2 md:col-span-6 relative group fade-in-up">
              <div className="tape-strip"></div>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                alt="Saturn Alignment"
                className="relative wobbly-border object-cover shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)] z-10 grayscale-transition h-[500px] w-full"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCHKwZX0AY5XsTm-WFNjLhkdkhgHziWWk5DNXamYRZbA3RN9RN3Uf4cu3JClH0AgTY1jQrIUWAwbdj1q-6EVgzeTw4OfgrS2N_JQ9h62ubfwGO4EYoJ8bFsPptfj-b0t8GDVCbUPyEdCPp6m4Y6pex6danZbcfm9r2m26Ld7ry_dv1sibZ4ObkgdNgDVbtP17rTAHqVDKHQ_VfLMFzrK_neAEOnW6doMW_Y7bmYSTAKk4UGcM0v-Et1NTjLjE4jp8yKIfy7EUnwnho"
              />
              <div className="absolute -left-10 top-1/2 -translate-y-1/2 vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
                EDITORIAL // 05
              </div>
            </div>
            <div className="col-span-4 md:col-start-9 md:col-span-3 space-y-6 mt-12 md:mt-0">
              <div className="glass-panel wobbly-border fade-in-up p-6 bg-surface-container-lowest" style={{ transitionDelay: '100ms' }}>
                <h3 className="font-headline-md text-2xl text-primary mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-solar-gold">timeline</span>
                  Petrova Alignments
                </h3>
                <p className="font-body-md text-on-surface-variant">
                  Our proprietary algorithms trace the geometric resonance between planetary bodies, visualizing stress points and energy conduits in your chart with sub-degree precision.
                </p>
              </div>
              <div className="glass-panel wobbly-border fade-in-up p-6 bg-surface-container-lowest" style={{ transitionDelay: '200ms' }}>
                <h3 className="font-headline-md text-2xl text-primary mb-3 flex items-center gap-2">
                  <span className="material-symbols-outlined text-solar-gold">radar</span>
                  Transit Analytics
                </h3>
                <p className="font-body-md text-on-surface-variant">
                  Real-time monitoring of celestial movements overlaying your natal coordinates, forecasting energetic shifts before they manifest in the physical realm.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 7. FAMILY VAULT & MUHURTA DASHBOARD */}
      <section className="py-32 px-margin-mobile md:px-margin-desktop z-10 relative border-t border-dashed border-outline/20">
        <div className="max-w-[1440px] mx-auto">
          <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter">
            {/* Family Vault */}
            <div className="col-span-4 md:col-start-2 md:col-span-6 fade-in-up glass-panel wobbly-border p-8 flex flex-col justify-between relative bg-surface-container-lowest shadow-[4px_4px_0px_0px_rgba(26,28,27,0.05)]">
              <div className="absolute -left-10 top-1/2 -translate-y-1/2 vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
                EDITORIAL // 07
              </div>
              <div>
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h2 className="font-headline-md text-3xl text-primary mb-2">
                      The Family <span className="font-annotation-sm text-4xl text-solar-gold">Vault</span>
                    </h2>
                    <p className="font-nav-label text-nav-label text-outline-variant uppercase tracking-widest">
                      SECURE KINSHIP DATA MATRIX
                    </p>
                  </div>
                  <span className="material-symbols-outlined text-solar-gold text-3xl">hub</span>
                </div>
                <p className="font-body-md text-on-surface-variant max-w-lg leading-relaxed">
                  Centralize the celestial coordinates of your entire lineage. Compare compatibility metrics across
                  generations, track shared transits, and identify deep karmic patterns within an encrypted, sovereign data
                  vault. Your family&apos;s astrological heritage, preserved and decoded forever.
                </p>
              </div>
              <div className="mt-8 flex gap-4">
                <div className="w-12 h-12 wobbly-border-sm bg-surface-container flex items-center justify-center text-xs font-nav-label text-on-surface">
                  P1
                </div>
                <div className="w-12 h-12 wobbly-border-sm bg-surface-container flex items-center justify-center text-xs font-nav-label text-on-surface">
                  P2
                </div>
                <div className="w-12 h-12 wobbly-border-sm border-dashed flex items-center justify-center text-outline-variant hover:text-primary transition-colors cursor-pointer">
                  <span className="material-symbols-outlined text-sm">add</span>
                </div>
              </div>
            </div>

            {/* Muhurta Status */}
            <div
              className="col-span-4 md:col-start-9 md:col-span-3 glass-panel wobbly-border fade-in-up p-8 relative bg-surface-container-lowest shadow-[4px_4px_0px_0px_rgba(26,28,27,0.05)] mt-12 md:mt-0"
              style={{ transitionDelay: '100ms' }}
            >
              <div className="tape-strip-right"></div>
              <h2 className="font-headline-md text-2xl text-primary mb-6">
                Muhurta <span className="font-annotation-sm text-3xl text-solar-gold">Status</span>
              </h2>
              <div className="space-y-4">
                <div className="flex justify-between items-center border-b border-dashed border-outline/20 pb-2">
                  <span className="font-body-md text-on-surface-variant">Current Window</span>
                  <span className="font-nav-label text-xs text-primary font-bold">SUB-OPTIMAL</span>
                </div>
                <div className="flex justify-between items-center border-b border-dashed border-outline/20 pb-2">
                  <span className="font-body-md text-on-surface-variant">Next Auspicious</span>
                  <span className="font-nav-label text-xs text-solar-gold">T+04:12:00</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="font-body-md text-on-surface-variant">Panchang Sync</span>
                  <span className="font-nav-label text-xs text-on-surface flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-solar-gold animate-pulse"></span>
                    ACTIVE
                  </span>
                </div>
              </div>
              <button className="mt-8 w-full py-3 border border-primary wobbly-border-sm text-primary font-nav-label text-xs uppercase tracking-widest hover:bg-secondary-container/10 hover:translate-x-1 hover:translate-y-1 transition-all">
                VIEW FULL DASHBOARD
              </button>
            </div>

            {/* Compassion / Safety Net */}
            <div
              className="col-span-4 md:col-start-2 md:col-span-10 fade-in-up glass-panel wobbly-border p-8 mt-12 bg-surface-container-low shadow-[4px_4px_0px_0px_rgba(26,28,27,0.05)]"
              style={{ transitionDelay: '200ms' }}
            >
              <div className="flex flex-col md:flex-row gap-8 items-center md:items-start">
                <div className="w-16 h-16 wobbly-border bg-surface-container flex items-center justify-center shrink-0 mt-2">
                  <span className="material-symbols-outlined text-3xl text-primary">health_and_safety</span>
                </div>
                <div>
                  <h2 className="font-headline-md text-2xl text-primary mb-4">The Safety Net Protocol</h2>
                  <p className="font-body-md text-on-surface-variant leading-relaxed">
                    Astrology should empower, not instill fear. Astrophage is programmed with deep empathic guardrails. We focus on remedies, potential, and spiritual growth—never fatalism. Complex transits are explained with the care of a wise elder, offering actionable light in the darkness. We identify the cosmic storm, but more importantly, we give you the umbrella.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
