"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, RefreshCw } from "lucide-react";
import {
  profilesApi,
  toolsApi,
  type BirthProfile,
  type SadeSatiResult,
  type NakshatraResult,
  type DailyTransits,
} from "@/lib/api";
import BirthChartCard from "@/components/cards/BirthChartCard";
import DashaTimelineCard from "@/components/cards/DashaTimelineCard";
import NakshatraCard from "@/components/cards/NakshatraCard";
import SadeSatiCard from "@/components/cards/SadeSatiCard";
import DailyTransitsCard from "@/components/cards/DailyTransitsCard";
import ChartSvgCard from "@/components/cards/ChartSvgCard";
import { useAppStore } from "@/lib/store";

export default function ProfileDetailPage() {
  const router = useRouter();
  const params = useParams();
  const profileId = params.id as string;

  const { user } = useAppStore();
  const [profile, setProfile] = useState<BirthProfile | null>(null);
  const [svg, setSvg] = useState<string>("");
  const [nak, setNak] = useState<NakshatraResult | null>(null);
  const [sade, setSade] = useState<SadeSatiResult | null>(null);
  const [transits, setTransits] = useState<DailyTransits | null>(null);
  const [loading, setLoading] = useState(true);
  const [recomputing, setRecomputing] = useState(false);

  const loadEverything = async (p: BirthProfile) => {
    if (!p.computed_chart) return;
    const style = user?.chart_format || "south_indian";
    try {
      const [svgRes, nakRes, sadeRes, transitRes] = await Promise.all([
        toolsApi.chartSvg(p.computed_chart, style),
        toolsApi.nakshatra(p.computed_chart),
        toolsApi.sadeSati(p.computed_chart),
        toolsApi.dailyTransits({ natal_chart: p.computed_chart }),
      ]);
      setSvg(svgRes.svg);
      setNak(nakRes);
      setSade(sadeRes);
      setTransits(transitRes);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    profilesApi
      .get(profileId)
      .then(async (p) => {
        setProfile(p);
        await loadEverything(p);
      })
      .catch(() => router.push("/family"))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId]);

  const handleRecompute = async () => {
    if (!profile) return;
    setRecomputing(true);
    try {
      const updated = await profilesApi.recompute(profile.id);
      setProfile(updated);
      await loadEverything(updated);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Recompute failed");
    } finally {
      setRecomputing(false);
    }
  };

  if (loading || !profile) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="w-3 h-3 rounded-full bg-solar-gold animate-pulse" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <Link
          href="/family"
          className="flex items-center gap-2 font-nav-label text-xs uppercase tracking-widest text-on-surface-variant hover:text-solar-gold"
        >
          <ArrowLeft size={14} />
          Vault
        </Link>
        <button
          onClick={handleRecompute}
          disabled={recomputing}
          className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50"
        >
          <RefreshCw size={12} className={recomputing ? "animate-spin" : ""} />
          {recomputing ? "Computing…" : "Recompute"}
        </button>
      </div>

      <div className="mb-6">
        <h1 className="font-headline-md text-3xl text-primary mb-1">
          {profile.name}
        </h1>
        <p className="font-body-md text-sm text-on-surface-variant">
          {profile.relationship && `${profile.relationship} · `}
          {profile.birth_date}
          {profile.birth_time && ` · ${profile.birth_time}`}
          {profile.place_name && ` · ${profile.place_name}`}
        </p>
      </div>

      {!profile.computed_chart && (
        <div className="glass-panel wobbly-border p-6 text-center">
          <p className="font-body-md text-sm text-on-surface-variant">
            Chart not yet computed. Click <strong>Recompute</strong> above.
          </p>
        </div>
      )}

      {profile.computed_chart && (
        <div className="space-y-6 w-full">
          {/* Pair 1: Visualization & Birth Chart */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
            {svg && (
              <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
                <ChartSvgCard svg={svg} />
              </div>
            )}
            <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
              <BirthChartCard data={profile.computed_chart} />
            </div>
          </div>

          {/* Pair 2: Dasha & Transits */}
          {(profile.computed_dashas || transits) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {profile.computed_dashas && (
                <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
                  <DashaTimelineCard data={profile.computed_dashas} />
                </div>
              )}
              {transits && (
                <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
                  <DailyTransitsCard data={transits} />
                </div>
              )}
            </div>
          )}

          {/* Pair 3: Sade Sati & Nakshatra */}
          {(sade || nak) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
              {sade && (
                <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
                  <SadeSatiCard data={sade} />
                </div>
              )}
              {nak && (
                <div className="flex justify-start w-full [&>div]:!max-w-none [&>div]:!w-full">
                  <NakshatraCard data={nak} />
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
