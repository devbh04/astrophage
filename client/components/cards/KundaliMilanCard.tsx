import { Heart } from "lucide-react";
import CardShell from "./CardShell";
import type { KundaliMilanResult } from "@/lib/api";

const KOOTA_MAX: Record<string, number> = {
  varna: 1,
  vashya: 2,
  tara: 3,
  yoni: 4,
  graha_maitri: 5,
  gana: 6,
  bhakoot: 7,
  nadi: 8,
};

const KOOTA_LABELS: Record<string, string> = {
  varna: "Varna",
  vashya: "Vashya",
  tara: "Tara",
  yoni: "Yoni",
  graha_maitri: "Graha Maitri",
  gana: "Gana",
  bhakoot: "Bhakoot",
  nadi: "Nadi",
};

const VERDICT_TONE: Record<string, string> = {
  excellent: "bg-emerald-300/25 text-emerald-700 border-emerald-400/60",
  good: "bg-sky-300/20 text-sky-700 border-sky-400/60",
  average: "bg-amber-300/20 text-amber-700 border-amber-400/60",
  low: "bg-rose-300/25 text-rose-700 border-rose-400/60",
};

interface Props {
  data: KundaliMilanResult;
  fullWidth?: boolean;
}

export default function KundaliMilanCard({ data, fullWidth }: Props) {
  // Defensive: if the tool errored or returned a partial payload, render a
  // friendly placeholder instead of crashing the whole page on
  // ``Object.entries(undefined)``.
  if (!data || typeof data !== "object" || !data.scores) {
    return (
      <CardShell
        title="Kundali Milan"
        badge="incomplete"
        icon={<Heart size={16} />}
        accent="rose"
        fullWidth={fullWidth}
      >
        <p className="font-body-md text-sm text-on-surface-variant">
          Could not compute the match. Please share the partner&apos;s full
          birth details (date, time, place) and try again.
        </p>
      </CardShell>
    );
  }

  const total = data.total ?? 0;
  const verdict = data.verdict || "average";
  const summary = data.summary || "";
  const mangal = data.mangal_dosha;
  const warnings = data.warnings || [];
  return (
    <CardShell
      title="Kundali Milan"
      badge={verdict}
      icon={<Heart size={16} />}
      accent="rose"
      fullWidth={fullWidth}
    >
      <div className="flex items-center gap-4 mb-5">
        <div
          className={`w-24 h-24 rounded-full flex flex-col items-center justify-center wobbly-border-sm ${
            VERDICT_TONE[verdict] || ""
          }`}
        >
          <div className="font-headline-md text-2xl">{total}</div>
          <div className="font-nav-label text-[9px] uppercase tracking-widest opacity-70">
            of 36
          </div>
        </div>
        <div className="flex-1">
          <div className="font-annotation-sm text-2xl text-solar-gold capitalize">
            {verdict}
          </div>
          {summary && (
            <p className="font-body-md text-xs text-on-surface-variant mt-1 italic">
              {summary}
            </p>
          )}
        </div>
      </div>

      {/* Koota score breakdown */}
      <div className="space-y-1.5 mb-4">
        {Object.entries(data.scores).map(([key, val]) => {
          const max = KOOTA_MAX[key] || 1;
          const numeric = Number(val) || 0;
          const pct = Math.min(100, Math.max(0, (numeric / max) * 100));
          const isFull = numeric === max;
          const isZero = numeric === 0;
          return (
            <div key={key} className="flex items-center gap-3">
              <div className="w-24 font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                {KOOTA_LABELS[key] || key}
              </div>
              <div className="flex-1 h-2.5 bg-surface-container-lowest/60 rounded-sm overflow-hidden border border-outline/20">
                <div
                  className={`h-full ${
                    isFull
                      ? "bg-emerald-500/60"
                      : isZero
                      ? "bg-rose-500/40"
                      : "bg-solar-gold/60"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <div className="w-10 text-right font-headline-md text-sm text-primary">
                {numeric}/{max}
              </div>
            </div>
          );
        })}
      </div>

      {mangal && mangal.boy && mangal.girl && (
        <div className="grid grid-cols-2 gap-2 mb-3">
          <DoshaCell
            who="Boy"
            present={!!mangal.boy.present}
            cancelled={!!mangal.boy.cancelled}
          />
          <DoshaCell
            who="Girl"
            present={!!mangal.girl.present}
            cancelled={!!mangal.girl.cancelled}
          />
        </div>
      )}

      {warnings.length > 0 && (
        <div className="bg-amber-500/10 wobbly-border-sm px-3 py-2">
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-amber-700 mb-1">
            Warnings
          </div>
          <ul className="space-y-0.5">
            {warnings.map((w, i) => (
              <li
                key={i}
                className="font-body-md text-[11px] text-on-surface-variant"
              >
                · {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </CardShell>
  );
}

function DoshaCell({
  who,
  present,
  cancelled,
}: {
  who: string;
  present: boolean;
  cancelled: boolean;
}) {
  const tone = !present
    ? "bg-emerald-500/5 text-emerald-700"
    : cancelled
    ? "bg-sky-500/5 text-sky-700"
    : "bg-rose-500/15 text-rose-700";
  const label = !present
    ? "no Mangal Dosha"
    : cancelled
    ? "Mangal — cancelled"
    : "Mangal Dosha";
  return (
    <div className={`px-3 py-2 wobbly-border-sm ${tone}`}>
      <div className="font-nav-label text-[9px] uppercase tracking-widest opacity-70">
        {who}
      </div>
      <div className="font-headline-md text-xs mt-0.5">{label}</div>
    </div>
  );
}
