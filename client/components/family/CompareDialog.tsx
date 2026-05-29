"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toolsApi, type BirthProfile, type KundaliMilanResult } from "@/lib/api";
import KundaliMilanCard from "@/components/cards/KundaliMilanCard";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profiles: BirthProfile[];
  initialBoyId?: string;
}

export default function CompareDialog({
  open,
  onOpenChange,
  profiles,
  initialBoyId,
}: Props) {
  const [boyId, setBoyId] = useState<string | undefined>(initialBoyId);
  const [girlId, setGirlId] = useState<string | undefined>();
  const [result, setResult] = useState<KundaliMilanResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const computable = profiles.filter((p) => !!p.computed_chart);

  const handleCompare = async () => {
    setError("");
    setResult(null);
    if (!boyId || !girlId || boyId === girlId) {
      setError("Pick two different profiles");
      return;
    }
    const boy = profiles.find((p) => p.id === boyId);
    const girl = profiles.find((p) => p.id === girlId);
    if (!boy?.computed_chart || !girl?.computed_chart) {
      setError("Both profiles need computed charts");
      return;
    }
    setLoading(true);
    try {
      const r = await toolsApi.kundaliMilan(
        boy.computed_chart,
        girl.computed_chart
      );
      setResult(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Compare failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-panel wobbly-border max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-headline-md text-xl text-primary">
            Compare Kundalis
          </DialogTitle>
        </DialogHeader>

        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="space-y-1.5">
            <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Profile A
            </div>
            <Select value={boyId} onValueChange={setBoyId}>
              <SelectTrigger className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md">
                <SelectValue placeholder="Choose…" />
              </SelectTrigger>
              <SelectContent className="bg-surface-container-lowest border-outline/30">
                {computable.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name} ({p.relationship || "—"})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Profile B
            </div>
            <Select value={girlId} onValueChange={setGirlId}>
              <SelectTrigger className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md">
                <SelectValue placeholder="Choose…" />
              </SelectTrigger>
              <SelectContent className="bg-surface-container-lowest border-outline/30">
                {computable.map((p) => (
                  <SelectItem key={p.id} value={p.id}>
                    {p.name} ({p.relationship || "—"})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-3">
          <button
            onClick={handleCompare}
            disabled={loading}
            className="btn-primary wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest disabled:opacity-50"
          >
            {loading ? "Computing…" : "Compute Milan"}
          </button>
        </div>

        {error && <p className="mt-3 text-rose-400 text-sm font-body-md">{error}</p>}

        {result && (
          <div className="mt-5">
            <KundaliMilanCard data={result} />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
