import { Sun, Moon, Clock } from "lucide-react";
import CardShell from "./CardShell";
import type { PanchangData } from "@/lib/api";

interface Props {
  data: PanchangData;
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

export default function PanchangCard({ data }: Props) {
  return (
    <CardShell title="Panchang" badge={data.vara?.weekday} icon={<Clock size={16} />} accent="gold">
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

      <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant mb-2">
        Inauspicious Windows
      </div>
      <div className="space-y-1.5 mb-4">
        <Window k="Rahu Kaal" tone="bg-rose-500/15 text-rose-300" v={`${fmtTime(data.rahu_kaal.start)} – ${fmtTime(data.rahu_kaal.end)}`} />
        <Window k="Yamaganda" tone="bg-amber-500/15 text-amber-300" v={`${fmtTime(data.yamaganda.start)} – ${fmtTime(data.yamaganda.end)}`} />
        <Window k="Gulika" tone="bg-violet-500/15 text-violet-300" v={`${fmtTime(data.gulika.start)} – ${fmtTime(data.gulika.end)}`} />
      </div>

      <div className="px-3 py-2 bg-emerald-500/10 wobbly-border-sm">
        <div className="font-nav-label text-[9px] uppercase tracking-widest text-emerald-300">
          Abhijit Muhurta · Auspicious
        </div>
        <div className="font-headline-md text-sm text-primary mt-1">
          {fmtTime(data.abhijit_muhurta.start)} – {fmtTime(data.abhijit_muhurta.end)}
        </div>
      </div>
    </CardShell>
  );
}

function Limb({ k, v, sub }: { k: string; v: string; sub?: string }) {
  return (
    <div className="bg-surface-container-low/60 wobbly-border-sm px-3 py-2">
      <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
        {k}
      </div>
      <div className="font-headline-md text-sm text-primary mt-0.5">{v}</div>
      {sub && (
        <div className="font-body-md text-[10px] text-on-surface-variant">
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
        <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
          {k}
        </div>
        <div className="font-headline-md text-sm text-primary">{v}</div>
      </div>
    </div>
  );
}

function Window({ k, v, tone }: { k: string; v: string; tone: string }) {
  return (
    <div className={`flex items-center justify-between px-3 py-1.5 rounded ${tone}`}>
      <span className="font-nav-label text-[10px] uppercase tracking-widest">
        {k}
      </span>
      <span className="font-body-md text-[11px]">{v}</span>
    </div>
  );
}
