"use client";

import { useState } from "react";
import { Clock4, ChevronDown, ChevronRight } from "lucide-react";
import CardShell from "./CardShell";
import type { ComputedDashas, DashaSegment } from "@/lib/api";

const LORD_COLOUR: Record<string, string> = {
  Ketu: "bg-rose-500/40 border-rose-400",
  Venus: "bg-pink-500/40 border-pink-400",
  Sun: "bg-amber-500/40 border-amber-400",
  Moon: "bg-sky-500/40 border-sky-400",
  Mars: "bg-red-500/40 border-red-400",
  Rahu: "bg-violet-500/40 border-violet-400",
  Jupiter: "bg-yellow-500/40 border-yellow-400",
  Saturn: "bg-slate-500/40 border-slate-400",
  Mercury: "bg-emerald-500/40 border-emerald-400",
};

interface Props {
  data: ComputedDashas;
}

const fmtYear = (iso: string) => {
  try {
    return new Date(iso).getFullYear().toString();
  } catch {
    return "—";
  }
};

export default function DashaTimelineCard({ data }: Props) {
  const [expanded, setExpanded] = useState<number | null>(null);
  const timeline = (data.timeline || []).slice(0, 12);
  const totalYears = timeline.reduce((sum, s) => sum + s.years, 0);

  const active = data.active?.maha;
  const activeAntar = data.active?.antar;

  return (
    <CardShell
      title="Vimshottari Dasha"
      badge={`Maha · ${active?.lord || "—"}`}
      icon={<Clock4 size={16} />}
      accent="violet"
    >
      <div className="mb-4 grid grid-cols-2 gap-2">
        <div className="bg-surface-container-low/60 wobbly-border-sm p-3">
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
            Active Mahadasha
          </div>
          <div className="font-headline-md text-base text-primary mt-1">
            {active?.lord || "—"}
          </div>
          {active && (
            <div className="font-body-md text-[11px] text-on-surface-variant mt-0.5">
              {fmtYear(active.start)} → {fmtYear(active.end)}
            </div>
          )}
        </div>
        <div className="bg-surface-container-low/60 wobbly-border-sm p-3">
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
            Active Antardasha
          </div>
          <div className="font-headline-md text-base text-primary mt-1">
            {activeAntar?.lord || "—"}
          </div>
          {activeAntar && (
            <div className="font-body-md text-[11px] text-on-surface-variant mt-0.5">
              {fmtYear(activeAntar.start)} → {fmtYear(activeAntar.end)}
            </div>
          )}
        </div>
      </div>

      {/* Stacked horizontal bar */}
      <div className="mb-4 h-3 w-full flex overflow-hidden wobbly-border-sm">
        {timeline.map((seg, i) => (
          <div
            key={i}
            title={`${seg.lord} · ${seg.years.toFixed(1)} yr`}
            style={{ width: `${(seg.years / totalYears) * 100}%` }}
            className={`${LORD_COLOUR[seg.lord] || "bg-surface-container border-outline"} h-full border-r last:border-r-0 border-background/60`}
          />
        ))}
      </div>

      <div className="space-y-1.5">
        {timeline.map((seg, i) => (
          <DashaRow
            key={i}
            seg={seg}
            isActive={
              !!active &&
              seg.lord === active.lord &&
              seg.start === active.start
            }
            expanded={expanded === i}
            onToggle={() => setExpanded(expanded === i ? null : i)}
          />
        ))}
      </div>
    </CardShell>
  );
}

function DashaRow({
  seg,
  isActive,
  expanded,
  onToggle,
}: {
  seg: DashaSegment;
  isActive: boolean;
  expanded: boolean;
  onToggle: () => void;
}) {
  const hasAntar = (seg.antardashas || []).length > 0;
  return (
    <div
      className={`wobbly-border-sm overflow-hidden ${
        isActive ? "ring-1 ring-solar-gold/60" : ""
      }`}
    >
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-3 py-2 bg-surface-container-low/40 hover:bg-surface-container/60 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              LORD_COLOUR[seg.lord]?.split(" ")[0] || "bg-outline"
            }`}
          />
          <span className="font-headline-md text-sm text-primary">
            {seg.lord}
          </span>
          <span className="font-body-md text-[11px] text-on-surface-variant">
            {fmtYear(seg.start)} – {fmtYear(seg.end)} · {seg.years.toFixed(1)} yr
          </span>
          {isActive && (
            <span className="px-1.5 py-0.5 text-[8px] font-nav-label uppercase tracking-wider bg-solar-gold/20 text-solar-gold rounded-sm">
              now
            </span>
          )}
        </div>
        {hasAntar && (
          <span className="text-on-surface-variant">
            {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          </span>
        )}
      </button>
      {expanded && hasAntar && (
        <div className="px-3 py-2 bg-surface-container-lowest/60 border-t border-outline/20 grid grid-cols-2 sm:grid-cols-3 gap-1">
          {(seg.antardashas || []).map((sub, j) => (
            <div
              key={j}
              className="flex items-center justify-between text-[11px] py-1"
            >
              <span className="font-headline-md text-primary">{sub.lord}</span>
              <span className="font-body-md text-on-surface-variant">
                {sub.years.toFixed(1)}y
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
