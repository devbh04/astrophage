"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export default function ChartPage() {
  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="font-headline-md text-2xl text-primary mb-2">
          Birth Chart <span className="font-annotation-sm text-3xl text-solar-gold">Viewer</span>
        </h2>
        <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
          YOUR CELESTIAL BLUEPRINT
        </p>
      </div>

      <Tabs defaultValue="natal" className="w-full">
        <TabsList className="bg-surface-container wobbly-border-sm p-1 mb-8">
          <TabsTrigger
            value="natal"
            className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
          >
            Natal Chart
          </TabsTrigger>
          <TabsTrigger
            value="dasha"
            className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
          >
            Dasha Timeline
          </TabsTrigger>
          <TabsTrigger
            value="transits"
            className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
          >
            Transits
          </TabsTrigger>
          <TabsTrigger
            value="nakshatra"
            className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
          >
            Nakshatra
          </TabsTrigger>
        </TabsList>

        <TabsContent value="natal">
          <div className="glass-panel wobbly-border p-8 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
                auto_awesome
              </span>
              <p className="font-annotation-sm text-lg text-solar-gold mb-2">
                Chart visualization coming soon
              </p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Your natal chart SVG will render here once computed via the chat.
              </p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="dasha">
          <div className="glass-panel wobbly-border p-8 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
                timeline
              </span>
              <p className="font-annotation-sm text-lg text-solar-gold mb-2">
                Dasha timeline visualization
              </p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Ask about your Dasha periods in the chat to populate this view.
              </p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="transits">
          <div className="glass-panel wobbly-border p-8 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
                radar
              </span>
              <p className="font-annotation-sm text-lg text-solar-gold mb-2">
                Current transits overlay
              </p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Real-time transit data will be overlaid on your natal chart.
              </p>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="nakshatra">
          <div className="glass-panel wobbly-border p-8 min-h-[400px] flex items-center justify-center">
            <div className="text-center">
              <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
                star
              </span>
              <p className="font-annotation-sm text-lg text-solar-gold mb-2">
                Nakshatra wheel
              </p>
              <p className="font-body-md text-sm text-on-surface-variant">
                Your birth star and its cosmic connections will appear here.
              </p>
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}
