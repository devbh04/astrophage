import { BookOpen } from "lucide-react";
import CardShell from "./CardShell";
import type { KnowledgeHit } from "@/lib/api";

interface Props {
  // The backend wraps the knowledge_lookup list result in `{hits: [...]}`
  // so it fits the ChatCard.data dict schema. Also accept a raw array
  // for backwards compatibility.
  data: { hits?: KnowledgeHit[] } | KnowledgeHit[];
}

export default function KnowledgeCard({ data }: Props) {
  const hits: KnowledgeHit[] = Array.isArray(data)
    ? data
    : (data?.hits || []);

  if (hits.length === 0) {
    return (
      <CardShell
        title="Sourced Wisdom"
        badge="0 passages"
        icon={<BookOpen size={16} />}
        accent="gold"
      >
        <p className="font-body-md text-[12px] text-on-surface-variant">
          No matching passages found in the knowledge base.
        </p>
      </CardShell>
    );
  }

  return (
    <CardShell
      title="Sourced Wisdom"
      badge={`${hits.length} passages`}
      icon={<BookOpen size={16} />}
      accent="gold"
    >
      <div className="space-y-2.5">
        {hits.map((hit, i) => (
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
