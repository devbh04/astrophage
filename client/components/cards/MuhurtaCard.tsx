import { Calendar, CheckCircle2 } from "lucide-react";
import CardShell from "./CardShell";
import type { MuhurtaWindow } from "@/lib/api";

interface Props {
  data: { purpose: string; windows: MuhurtaWindow[] };
  fullWidth?: boolean;
}

const fmtDateTime = (iso: string) => {
  try {
    const d = new Date(iso);
    return {
      date: d.toLocaleDateString(undefined, {
        weekday: "short",
        day: "numeric",
        month: "short",
      }),
      time: d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };
  } catch {
    return { date: "—", time: "—" };
  }
};

export default function MuhurtaCard({ data, fullWidth }: Props) {
  return (
    <CardShell
      title="Auspicious Muhurta"
      badge={data.purpose}
      icon={<Calendar size={16} />}
      accent="teal"
      fullWidth={fullWidth}
    >
      {data.windows.length === 0 ? (
        <p className="font-body-md text-sm text-on-surface-variant text-center py-4">
          No clean windows found in this range. Try widening the date range.
        </p>
      ) : (
        <div className="space-y-3">
          {data.windows.map((w, i) => {
            const start = fmtDateTime(w.start);
            const end = fmtDateTime(w.end);
            const pct = Math.round(w.score * 100);
            return (
              <div
                key={i}
                className="bg-surface-container-low/60 wobbly-border-sm overflow-hidden"
              >
                <div className="flex items-stretch">
                  <div className="w-16 bg-emerald-500/10 flex flex-col items-center justify-center text-center py-3 border-r border-outline/20">
                    <CheckCircle2
                      size={14}
                      className="text-emerald-400 mb-1"
                    />
                    <div className="font-headline-md text-base text-emerald-300">
                      {pct}
                    </div>
                    <div className="font-nav-label text-[8px] uppercase tracking-widest text-on-surface-variant">
                      score
                    </div>
                  </div>
                  <div className="flex-1 p-3">
                    <div className="font-headline-md text-sm text-primary">
                      {start.date}
                    </div>
                    <div className="font-body-md text-xs text-on-surface-variant mb-2">
                      {start.time} – {end.time} · {w.duration_minutes}m
                    </div>
                    <p className="font-body-md text-[11px] text-on-surface italic">
                      {w.summary}
                    </p>
                  </div>
                </div>
                <div className="px-3 py-2 bg-surface-container/40 grid grid-cols-3 gap-1 text-[10px]">
                  <Factor k="Tithi" v={w.factors.tithi} />
                  <Factor k="Nak" v={w.factors.nakshatra} />
                  <Factor k="Yoga" v={w.factors.yoga} />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </CardShell>
  );
}

function Factor({ k, v }: { k: string; v: string }) {
  return (
    <div className="text-center">
      <div className="font-nav-label text-[8px] uppercase tracking-widest text-on-surface-variant">
        {k}
      </div>
      <div className="font-body-md text-[10px] text-primary break-words">{v}</div>
    </div>
  );
}
