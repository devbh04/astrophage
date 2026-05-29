import { Globe2 } from "lucide-react";
import CardShell from "./CardShell";
import type { CurrentSky } from "@/lib/api";

const PLANET_GLYPH: Record<string, string> = {
  Sun: "☉",
  Moon: "☽",
  Mars: "♂",
  Mercury: "☿",
  Jupiter: "♃",
  Venus: "♀",
  Saturn: "♄",
  Rahu: "☊",
  Ketu: "☋",
};

interface Props {
  data: CurrentSky;
}

const fmt = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
    });
  } catch {
    return "—";
  }
};

export default function CurrentSkyCard({ data }: Props) {
  const illum = Math.round(data.moon_phase.illumination * 100);
  return (
    <CardShell
      title="Current Sky"
      badge={data.moon_phase.name}
      icon={<Globe2 size={16} />}
      accent="teal"
    >
      <div className="flex items-center gap-4 mb-5">
        <div className="relative w-16 h-16">
          <div className="absolute inset-0 rounded-full bg-surface-container border border-outline/40" />
          <div
            className="absolute inset-0 rounded-full bg-solar-gold/70"
            style={{
              clipPath: `inset(0 ${100 - illum}% 0 0)`,
            }}
          />
        </div>
        <div className="flex-1">
          <div className="font-headline-md text-base text-primary">
            {data.moon_phase.name}
          </div>
          <div className="font-body-md text-xs text-on-surface-variant">
            Illumination · {illum}%
          </div>
          <div className="font-body-md text-[11px] text-on-surface-variant mt-1">
            Full → {fmt(data.moon_phase.next_full_moon)} · New →{" "}
            {fmt(data.moon_phase.next_new_moon)}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-1.5 mb-4">
        {data.planets.map((p) => (
          <div
            key={p.name}
            className="bg-surface-container-low/60 wobbly-border-sm px-2 py-1.5 text-center"
          >
            <div className="text-solar-gold text-base leading-none">
              {PLANET_GLYPH[p.name] || "✦"}
            </div>
            <div className="font-headline-md text-[11px] text-primary mt-0.5">
              {p.name}
              {p.retrograde && (
                <span className="ml-1 text-[8px] text-rose-400">(R)</span>
              )}
            </div>
            <div className="font-body-md text-[10px] text-on-surface-variant">
              {p.sign} · {p.degree.toFixed(1)}°
            </div>
          </div>
        ))}
      </div>

      {data.next_sign_change && (
        <div className="px-3 py-2 bg-violet-500/10 wobbly-border-sm">
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-violet-300">
            Next Sign Change
          </div>
          <div className="font-body-md text-sm text-primary mt-0.5">
            {data.next_sign_change.planet}: {data.next_sign_change.from} →{" "}
            {data.next_sign_change.to}{" "}
            <span className="text-on-surface-variant">
              · {fmt(data.next_sign_change.at)}
            </span>
          </div>
        </div>
      )}
    </CardShell>
  );
}
