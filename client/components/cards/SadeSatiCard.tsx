import { TriangleAlert, ShieldCheck } from "lucide-react";
import CardShell from "./CardShell";
import type { SadeSatiResult } from "@/lib/api";

interface Props {
  data: SadeSatiResult;
}

const PHASE_COPY: Record<string, { label: string; tone: string }> = {
  rising: { label: "Rising", tone: "bg-amber-500/20 text-amber-300" },
  peak: { label: "Peak", tone: "bg-rose-500/25 text-rose-300" },
  setting: { label: "Setting", tone: "bg-sky-500/20 text-sky-300" },
  none: { label: "Clear", tone: "bg-emerald-500/15 text-emerald-300" },
};

const fmt = (iso: string | null) => {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
    });
  } catch {
    return "—";
  }
};

export default function SadeSatiCard({ data }: Props) {
  const phase = PHASE_COPY[data.phase] || PHASE_COPY.none;
  return (
    <CardShell
      title="Sade Sati Status"
      badge={data.in_sade_sati ? "Active" : "Clear"}
      icon={data.in_sade_sati ? <TriangleAlert size={16} /> : <ShieldCheck size={16} />}
      accent={data.in_sade_sati ? "rose" : "teal"}
    >
      <div className="flex items-start gap-4 mb-4">
        <div
          className={`w-20 h-20 rounded-full flex items-center justify-center font-headline-md text-sm wobbly-border-sm ${phase.tone}`}
        >
          {phase.label}
        </div>
        <div className="flex-1">
          <p className="font-body-md text-sm text-on-surface leading-relaxed">
            {data.current_status}
          </p>
          {data.ashtama_shani && (
            <p className="mt-2 px-2 py-1 inline-block bg-amber-500/15 text-amber-300 text-[11px] font-nav-label uppercase tracking-wider rounded">
              Ashtama Shani
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2 mb-4">
        <Window k="Start" v={fmt(data.start)} />
        <Window k="Peak" v={fmt(data.peak_start)} />
        <Window k="End" v={fmt(data.end)} />
      </div>

      {data.history?.length > 0 && (
        <div>
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant mb-2">
            Past Occurrences
          </div>
          <div className="space-y-1">
            {data.history.slice(-3).map((h, i) => (
              <div
                key={i}
                className="flex items-center justify-between text-[11px] px-3 py-1.5 bg-surface-container-low/60 rounded"
              >
                <span className="font-body-md text-on-surface-variant">
                  {fmt(h.start)} → {fmt(h.end)}
                </span>
                <span className="font-nav-label text-[9px] uppercase tracking-wider text-solar-gold">
                  {h.phase} · {h.intensity}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </CardShell>
  );
}

function Window({ k, v }: { k: string; v: string }) {
  return (
    <div className="bg-surface-container-low/60 wobbly-border-sm py-2 px-3 text-center">
      <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
        {k}
      </div>
      <div className="font-headline-md text-sm text-primary">{v}</div>
    </div>
  );
}
