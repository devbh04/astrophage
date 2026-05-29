import CardShell from "./CardShell";
import { Sparkles } from "lucide-react";
import type { NatalChart, Planet } from "@/lib/api";

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
  data: NatalChart;
}

export default function BirthChartCard({ data }: Props) {
  const planets: Planet[] = data.planets || [];
  return (
    <CardShell
      title="Birth Chart"
      badge={data.ayanamsa || "Lahiri"}
      icon={<Sparkles size={16} />}
      accent="gold"
    >
      <div className="grid grid-cols-3 gap-3 mb-5">
        <Pill label="Sun" value={data.sun_sign} />
        <Pill label="Moon" value={data.moon_sign} />
        <Pill label="Lagna" value={data.ascendant?.sign || "—"} />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {planets.map((p) => (
          <div
            key={p.name}
            className="flex items-center justify-between px-3 py-2 bg-surface-container-low/60 wobbly-border-sm"
          >
            <div className="flex items-center gap-2">
              <span className="text-solar-gold text-lg leading-none">
                {PLANET_GLYPH[p.name] || "✦"}
              </span>
              <div>
                <div className="font-headline-md text-sm text-primary leading-tight">
                  {p.name}
                  {p.retrograde && (
                    <span className="ml-1 text-[10px] text-rose-400 font-nav-label">
                      (R)
                    </span>
                  )}
                </div>
                <div className="font-body-md text-xs text-on-surface-variant">
                  {p.sign}
                  {p.house ? ` · H${p.house}` : ""}
                </div>
              </div>
            </div>
            {p.nakshatra && (
              <div className="text-right">
                <div className="font-nav-label text-[9px] uppercase tracking-wider text-on-surface-variant">
                  NAKSHATRA
                </div>
                <div className="font-body-md text-xs text-primary">
                  {p.nakshatra}
                  {p.pada ? ` · ${p.pada}` : ""}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </CardShell>
  );
}

function Pill({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center bg-surface-container wobbly-border-sm py-3">
      <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
        {label}
      </div>
      <div className="font-headline-md text-base text-primary mt-1">
        {value}
      </div>
    </div>
  );
}
