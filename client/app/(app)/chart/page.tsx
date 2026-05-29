"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  profilesApi,
  toolsApi,
  type BirthProfile,
  type NakshatraResult,
  type DailyTransits,
} from "@/lib/api";
import { useAppStore } from "@/lib/store";
import BirthChartCard from "@/components/cards/BirthChartCard";
import DashaTimelineCard from "@/components/cards/DashaTimelineCard";
import NakshatraCard from "@/components/cards/NakshatraCard";
import DailyTransitsCard from "@/components/cards/DailyTransitsCard";
import ChartSvgCard from "@/components/cards/ChartSvgCard";

export default function ChartPage() {
  const { user } = useAppStore();
  const [self, setSelf] = useState<BirthProfile | null>(null);
  const [svg, setSvg] = useState<string>("");
  const [nak, setNak] = useState<NakshatraResult | null>(null);
  const [transits, setTransits] = useState<DailyTransits | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    profilesApi
      .list()
      .then(async (profiles) => {
        const me = profiles.find((p) => p.relationship === "self") || null;
        setSelf(me);
        if (me?.computed_chart) {
          const style = user?.chart_format || "south_indian";
          const [svgRes, nakRes, transitRes] = await Promise.all([
            toolsApi.chartSvg(me.computed_chart, style),
            toolsApi.nakshatra(me.computed_chart),
            toolsApi.dailyTransits({ natal_chart: me.computed_chart }),
          ]);
          setSvg(svgRes.svg);
          setNak(nakRes);
          setTransits(transitRes);
        }
      })
      .finally(() => setLoading(false));
  }, [user?.chart_format]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="w-3 h-3 rounded-full bg-solar-gold animate-pulse" />
      </div>
    );
  }

  if (!self) {
    return (
      <div className="p-6 md:p-8 max-w-3xl mx-auto">
        <div className="glass-panel wobbly-border p-12 text-center">
          <p className="font-annotation-sm text-2xl text-solar-gold mb-3">
            No self-profile yet
          </p>
          <p className="font-body-md text-sm text-on-surface-variant mb-6">
            Add a profile with relationship <strong>self</strong> in the Family
            Vault to populate this view.
          </p>
          <Link
            href="/family"
            className="btn-primary wobbly-border-sm inline-block px-5 py-3 font-nav-label text-[10px] uppercase tracking-widest"
          >
            Open Family Vault
          </Link>
        </div>
      </div>
    );
  }

  if (!self.computed_chart) {
    return (
      <div className="p-6 md:p-8 max-w-3xl mx-auto">
        <div className="glass-panel wobbly-border p-8 text-center">
          <p className="font-body-md text-sm text-on-surface-variant mb-4">
            Your chart hasn&apos;t been computed yet.
          </p>
          <button
            onClick={async () => {
              const updated = await profilesApi.recompute(self.id);
              setSelf(updated);
            }}
            className="btn-primary wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest"
          >
            Compute now
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 w-full">
      <Tabs defaultValue="natal" className="w-full">
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 gap-4">
          <div>
            <h2 className="font-headline-md text-2xl text-primary mb-2">
              Birth Chart{" "}
              <span className="font-annotation-sm text-3xl text-solar-gold">
                Viewer
              </span>
            </h2>
            <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
              {self.name.toUpperCase()} · {self.birth_date}
              {self.birth_time ? ` · ${self.birth_time}` : ""}
            </p>
          </div>

          <TabsList className="bg-surface-container wobbly-border-sm p-1 h-auto">
            <TabsTrigger
              value="natal"
              className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
            >
              Natal
            </TabsTrigger>
            <TabsTrigger
              value="dasha"
              className="font-nav-label text-xs uppercase tracking-wider data-[state=active]:bg-surface-container-lowest data-[state=active]:text-primary"
            >
              Dasha
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
        </div>

        <TabsContent value="natal" className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
          {svg && (
            <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
              <ChartSvgCard svg={svg} />
            </div>
          )}
          <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
            <BirthChartCard data={self.computed_chart} />
          </div>
        </TabsContent>

        <TabsContent value="dasha">
          {self.computed_dashas ? (
            <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
              <DashaTimelineCard data={self.computed_dashas} />
            </div>
          ) : (
            <p className="font-body-md text-sm text-on-surface-variant">
              No dasha data — recompute the profile.
            </p>
          )}
        </TabsContent>

        <TabsContent value="transits">
          {transits ? (
            <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
              <DailyTransitsCard data={transits} />
            </div>
          ) : (
            <p className="font-body-md text-sm text-on-surface-variant">
              Loading transits…
            </p>
          )}
        </TabsContent>

        <TabsContent value="nakshatra">
          {nak ? (
            <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
              <NakshatraCard data={nak} />
            </div>
          ) : (
            <p className="font-body-md text-sm text-on-surface-variant">
              Loading nakshatra…
            </p>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
