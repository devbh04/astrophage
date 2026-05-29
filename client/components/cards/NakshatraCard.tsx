import { Star } from "lucide-react";
import CardShell from "./CardShell";
import type { NakshatraResult } from "@/lib/api";

interface Props {
  data: NakshatraResult;
}

export default function NakshatraCard({ data }: Props) {
  return (
    <CardShell
      title="Janma Nakshatra"
      badge={`Pada ${data.pada}`}
      icon={<Star size={16} />}
      accent="gold"
    >
      <div className="text-center mb-5">
        <div className="font-annotation-sm text-3xl text-solar-gold">
          {data.janma_nakshatra}
        </div>
        <div className="font-body-md text-xs text-on-surface-variant mt-1">
          Lord: {data.lord} · Deity: {data.deity}
        </div>
        <div className="font-body-md text-xs text-on-surface-variant italic mt-1">
          {data.symbol}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-4">
        <Attr k="Gana" v={data.gana} />
        <Attr k="Yoni" v={data.yoni} />
        <Attr k="Nadi" v={data.nadi} />
        <Attr k="Varna" v={data.varna} />
        <Attr k="Tatva" v={data.tatva} />
        <Attr k="Lord" v={data.lord} />
      </div>

      <div className="mb-3">
        <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant mb-2">
          Lucky
        </div>
        <div className="flex flex-wrap gap-1.5">
          {data.lucky_colors.map((c) => (
            <span
              key={c}
              className="px-2 py-0.5 text-[10px] font-body-md bg-surface-container rounded-full"
            >
              {c}
            </span>
          ))}
          {data.lucky_numbers.map((n) => (
            <span
              key={n}
              className="px-2 py-0.5 text-[10px] font-body-md bg-solar-gold/15 text-solar-gold rounded-full"
            >
              {n}
            </span>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-emerald-400 mb-1">
            Compatible
          </div>
          <div className="font-body-md text-[11px] text-on-surface-variant">
            {data.compatible_nakshatras.slice(0, 5).join(", ") || "—"}
          </div>
        </div>
        <div>
          <div className="font-nav-label text-[9px] uppercase tracking-widest text-rose-400 mb-1">
            Avoid
          </div>
          <div className="font-body-md text-[11px] text-on-surface-variant">
            {data.incompatible_nakshatras.slice(0, 5).join(", ") || "—"}
          </div>
        </div>
      </div>
    </CardShell>
  );
}

function Attr({ k, v }: { k: string; v: string }) {
  return (
    <div className="bg-surface-container-low/60 wobbly-border-sm px-3 py-2">
      <div className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
        {k}
      </div>
      <div className="font-headline-md text-sm text-primary mt-0.5">{v}</div>
    </div>
  );
}
