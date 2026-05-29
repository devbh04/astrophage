import { BookOpen } from "lucide-react";
import CardShell from "./CardShell";
import type { KnowledgeHit } from "@/lib/api";

interface Props {
  data: KnowledgeHit[];
}

export default function KnowledgeCard({ data }: Props) {
  return (
    <CardShell
      title="Sourced Wisdom"
      badge={`${data.length} passages`}
      icon={<BookOpen size={16} />}
      accent="gold"
    >
      <div className="space-y-2.5">
        {data.map((hit, i) => (
          <div
            key={hit.chunk_id || i}
            className="bg-surface-container-low/60 wobbly-border-sm p-3"
          >
            <div className="flex items-center justify-between mb-1.5">
              <div className="font-nav-label text-[9px] uppercase tracking-widest text-solar-gold truncate">
                {hit.source}
              </div>
              <div className="font-body-md text-[10px] text-on-surface-variant">
                {(hit.score * 100).toFixed(0)}%
              </div>
            </div>
            <p className="font-body-md text-[12px] text-on-surface leading-relaxed line-clamp-3">
              {hit.text}
            </p>
          </div>
        ))}
      </div>
    </CardShell>
  );
}
