import { Sun, Moon, Clock, ArrowRight } from "lucide-react";
import CardShell from "./CardShell";
import type { PanchangData } from "@/lib/api";

interface Props {
  data: PanchangData;
  fullWidth?: boolean;
}

const fmtTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
};

export default function PanchangCard({ data, fullWidth }: Props) {
  return (
    <CardShell title="Panchang" badge={data.vara?.weekday} icon={<Clock size={16} />} accent="gold" fullWidth={fullWidth}>
      <div className="grid grid-cols-2 gap-2 mb-4">
        <Limb k="Tithi" v={data.tithi.name} sub={`#${data.tithi.number}`} />
        <Limb k="Nakshatra" v={data.nakshatra.name} sub={data.nakshatra.lord} />
        <Limb k="Yoga" v={data.yoga.name} sub={`#${data.yoga.number}`} />
        <Limb k="Karana" v={data.karana.name} />
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <SunPill icon={<Sun size={12} />} k="Sunrise" v={fmtTime(data.sunrise)} />
        <SunPill icon={<Moon size={12} />} k="Sunset" v={fmtTime(data.sunset)} />
      </div>

      <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant mb-2">
        Inauspicious Windows
      </div>
      <div className="space-y-2 mb-4">
        <Window
          k="Rahu Kaal"
          tone="bg-rose-500/5 text-rose-600 border-rose-500/30"
          start={fmtTime(data.rahu_kaal.start)}
          end={fmtTime(data.rahu_kaal.end)}
        />
        <Window
          k="Yamaganda"
          tone="bg-amber-500/5 text-amber-600 border-amber-500/30"
          start={fmtTime(data.yamaganda.start)}
          end={fmtTime(data.yamaganda.end)}
        />
        <Window
          k="Gulika"
          tone="bg-violet-500/5 text-violet-600 border-violet-500/30"
          start={fmtTime(data.gulika.start)}
          end={fmtTime(data.gulika.end)}
        />
      </div>
      <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant mb-2">
        Auspicious Windows
      </div>
      <div className="px-3 py-3 bg-emerald-500/5 wobbly-border-sm border border-emerald-500/30">
        <div className="font-nav-label text-xs uppercase tracking-widest text-emerald-700 mb-1.5 text-center">
          Abhijit Muhurta
        </div>
        <div className="flex items-center justify-center gap-3">
          <Tag label="Start" value={fmtTime(data.abhijit_muhurta.start)} tone="text-emerald-600" />
          <ArrowRight size={12} className="text-emerald-400/60" />
          <Tag label="End" value={fmtTime(data.abhijit_muhurta.end)} tone="text-emerald-600" />
        </div>
      </div>
    </CardShell>
  );
}

function Limb({ k, v, sub }: { k: string; v: string; sub?: string }) {
  return (
    <div className="bg-surface-container-low/60 wobbly-border-sm px-3 py-2">
      <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
        {k}
      </div>
      <div className="font-headline-md text-base text-primary mt-0.5">{v}</div>
      {sub && (
        <div className="font-body-md text-[11px] text-on-surface-variant">
          {sub}
        </div>
      )}
    </div>
  );
}

function SunPill({ icon, k, v }: { icon: React.ReactNode; k: string; v: string }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2 bg-surface-container wobbly-border-sm">
      <span className="text-solar-gold">{icon}</span>
      <div>
        <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
          {k}
        </div>
        <div className="font-headline-md text-base text-primary">{v}</div>
      </div>
    </div>
  );
}

function Window({
  k,
  start,
  end,
  tone,
}: {
  k: string;
  start: string;
  end: string;
  tone: string;
}) {
  return (
    <div className={`px-3 py-2 wobbly-border-sm border ${tone}`}>
      <div className="font-nav-label text-xs uppercase tracking-widest mb-1.5 text-center">
        {k}
      </div>
      <div className="flex items-center justify-center gap-3">
        <Tag label="Start" value={start} />
        <ArrowRight size={12} className="opacity-60" />
        <Tag label="End" value={end} />
      </div>
    </div>
  );
}

function Tag({ label, value, tone }: { label: string; value: string; tone?: string }) {
  return (
    <div className="flex items-baseline gap-1.5">
      <span className="font-nav-label text-xs uppercase tracking-widest opacity-60">
        {label}
      </span>
      <span className={`font-nav-md text-xs ${tone || ""}`}>{value}</span>
    </div>
  );
}
