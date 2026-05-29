import { Radar } from "lucide-react";
import CardShell from "./CardShell";
import type { DailyTransits } from "@/lib/api";

interface Props {
  data: DailyTransits;
}

const INTENSITY_TONE: Record<string, string> = {
  high: "bg-rose-500/10 text-rose-700",
  medium: "bg-amber-500/5 text-amber-700",
  low: "bg-sky-500/5 text-sky-700",
};

export default function DailyTransitsCard({ data }: Props) {
  return (
    <CardShell
      title="Today's Transits"
      badge={`${data.activated_houses?.length || 0} houses active`}
      icon={<Radar size={16} />}
      accent="violet"
    >
      <p className="font-annotation-sm text-base text-solar-gold mb-4 italic">
        {data.headline}
      </p>

      {/* House lights row */}
      <div className="mb-4">
        <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant mb-2">
          Activated Houses
        </div>
        <div className="grid grid-cols-12 gap-1">
          {Array.from({ length: 12 }, (_, i) => i + 1).map((h) => {
            const isActive = data.activated_houses?.includes(h);
            return (
              <div
                key={h}
                className={`aspect-square wobbly-border-sm flex items-center justify-center text-[16px] font-nav-label ${
                  isActive
                    ? "bg-solar-gold/10 text-amber-700 border-solar-gold/60"
                    : "bg-surface-container-low/40 text-outline-variant"
                }`}
                title={`House ${h}`}
              >
                {h}
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        {data.transits.slice(0, 9).map((t) => (
          <div
            key={t.planet}
            className="flex items-center gap-3 px-3 py-2 bg-surface-container-low/60 wobbly-border-sm"
          >
            <div className="w-14">
              <div className="font-headline-md text-sm text-primary">
                {t.planet}
                {t.retrograde && (
                  <span className="ml-1 text-[9px] text-rose-400">(R)</span>
                )}
              </div>
            </div>
            <div className="flex-1 text-[11px] font-body-md text-on-surface-variant truncate">
              {t.current_sign} · H{t.current_house_from_lagna}
              <span className="text-outline-variant"> · natal </span>
              {t.natal_sign} · H{t.natal_house}
            </div>
            <span
              className={`px-1.5 py-0.5 text-[9px] font-nav-label uppercase tracking-widest rounded ${
                INTENSITY_TONE[t.intensity]
              }`}
            >
              {t.intensity}
            </span>
          </div>
        ))}
      </div>
    </CardShell>
  );
}
