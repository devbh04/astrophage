import { Wrench, Check, Loader2, AlertTriangle } from "lucide-react";

export interface ToolRun {
  tool: string;
  args?: unknown;
  status?: "ok" | "running" | "error";
}

interface Props {
  runs: ToolRun[];
}

const TOOL_LABELS: Record<string, string> = {
  compute_birth_chart: "Birth chart",
  geocode_place: "Geocode place",
  compute_dasha_periods: "Dasha periods",
  compute_nakshatra_details: "Nakshatra",
  check_sade_sati: "Sade Sati",
  get_panchang: "Panchang",
  knowledge_lookup: "Knowledge lookup",
  kundali_milan: "Kundali Milan",
  render_chart_svg: "Chart SVG",
  compute_muhurta: "Muhurta",
  get_daily_transits: "Daily transits",
  get_current_sky: "Current sky",
};

function labelFor(name: string): string {
  return TOOL_LABELS[name] || name.replace(/_/g, " ");
}

function StatusIcon({ status }: { status?: ToolRun["status"] }) {
  if (status === "running")
    return <Loader2 size={10} className="animate-spin text-solar-gold" />;
  if (status === "error")
    return <AlertTriangle size={10} className="text-rose-400" />;
  return <Check size={10} className="text-emerald-400" />;
}

export default function ToolBadgeStrip({ runs }: Props) {
  if (!runs || runs.length === 0) return null;

  // De-duplicate consecutive identical tool runs (in case the same tool ran twice)
  const deduped: ToolRun[] = [];
  for (const r of runs) {
    if (
      deduped.length > 0 &&
      deduped[deduped.length - 1].tool === r.tool &&
      deduped[deduped.length - 1].status === r.status
    ) {
      continue;
    }
    deduped.push(r);
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1.5">
      <span className="flex items-center gap-1 font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant pr-1">
        <Wrench size={10} className="text-solar-gold/70" />
        Used
      </span>
      {deduped.map((r, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 px-2 py-0.5 wobbly-border-sm bg-surface-container-low/70 border border-outline/30 text-[10px] font-body-md text-on-surface-variant"
          title={
            r.args
              ? `args: ${JSON.stringify(r.args).slice(0, 200)}`
              : undefined
          }
        >
          <StatusIcon status={r.status} />
          <span className="font-headline-md">{labelFor(r.tool)}</span>
        </span>
      ))}
    </div>
  );
}
