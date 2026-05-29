"use client";

import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  toolsApi,
  profilesApi,
  type BirthProfile,
  type NatalChart,
  type KundaliMilanResult,
} from "@/lib/api";
import KundaliMilanCard from "@/components/cards/KundaliMilanCard";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  profiles: BirthProfile[];
  initialBoyId?: string;
  onProfileAdded?: (p: BirthProfile) => void;
}

type SourceMode = "stored" | "custom";

interface CustomInput {
  name: string;
  birthDate: string;
  birthTime: string;
  placeName: string;
  resolvedLat: number | null;
  resolvedLng: number | null;
  resolvedTz: string;
  resolvedPlace: string;
  addToVault: boolean;
}

const emptyCustom = (): CustomInput => ({
  name: "",
  birthDate: "",
  birthTime: "",
  placeName: "",
  resolvedLat: null,
  resolvedLng: null,
  resolvedTz: "",
  resolvedPlace: "",
  addToVault: false,
});

export default function CompareDialog({
  open,
  onOpenChange,
  profiles,
  initialBoyId,
  onProfileAdded,
}: Props) {
  const [modeA, setModeA] = useState<SourceMode>("stored");
  const [modeB, setModeB] = useState<SourceMode>("stored");
  const [storedIdA, setStoredIdA] = useState<string | undefined>(initialBoyId);
  const [storedIdB, setStoredIdB] = useState<string | undefined>();
  const [customA, setCustomA] = useState<CustomInput>(emptyCustom());
  const [customB, setCustomB] = useState<CustomInput>(emptyCustom());
  const [resolvingA, setResolvingA] = useState(false);
  const [resolvingB, setResolvingB] = useState(false);
  const [result, setResult] = useState<KundaliMilanResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [namesUsed, setNamesUsed] = useState<{ a: string; b: string }>({
    a: "",
    b: "",
  });

  // Sync initialBoyId when it changes
  useEffect(() => {
    if (initialBoyId) {
      setModeA("stored");
      setStoredIdA(initialBoyId);
    }
  }, [initialBoyId]);

  const computable = profiles.filter((p) => !!p.computed_chart);

  const resolvePlace = async (
    side: "a" | "b",
    custom: CustomInput,
    setCustom: (c: CustomInput) => void,
    setResolving: (b: boolean) => void
  ) => {
    if (!custom.placeName.trim()) return;
    setResolving(true);
    try {
      const r = await toolsApi.geocode(custom.placeName.trim());
      setCustom({
        ...custom,
        resolvedLat: r.lat,
        resolvedLng: r.lng,
        resolvedTz: r.timezone,
        resolvedPlace: r.canonical_name,
      });
    } catch (err) {
      setError(
        `Could not resolve place for Person ${side.toUpperCase()}: ${
          err instanceof Error ? err.message : "unknown"
        }`
      );
    } finally {
      setResolving(false);
    }
  };

  const getChart = async (
    mode: SourceMode,
    storedId: string | undefined,
    custom: CustomInput
  ): Promise<{ chart: NatalChart; name: string } | null> => {
    if (mode === "stored") {
      const p = profiles.find((pr) => pr.id === storedId);
      if (!p?.computed_chart) return null;
      return { chart: p.computed_chart, name: p.name };
    }
    // custom
    if (!custom.birthDate || custom.resolvedLat === null) return null;
    const chart = await toolsApi.birthChart({
      birth_date: custom.birthDate,
      birth_time: custom.birthTime || undefined,
      lat: custom.resolvedLat,
      lng: custom.resolvedLng!,
      timezone: custom.resolvedTz,
    });
    return { chart, name: custom.name || "Person" };
  };

  const handleCompare = async () => {
    setError("");
    setResult(null);

    // Validate
    if (modeA === "stored" && !storedIdA) {
      setError("Select Person A");
      return;
    }
    if (modeB === "stored" && !storedIdB) {
      setError("Select Person B");
      return;
    }
    if (
      modeA === "stored" &&
      modeB === "stored" &&
      storedIdA === storedIdB
    ) {
      setError("Pick two different profiles");
      return;
    }
    if (modeA === "custom" && (!customA.birthDate || customA.resolvedLat === null)) {
      setError("Fill and resolve Person A details");
      return;
    }
    if (modeB === "custom" && (!customB.birthDate || customB.resolvedLat === null)) {
      setError("Fill and resolve Person B details");
      return;
    }

    setLoading(true);
    try {
      const [chartA, chartB] = await Promise.all([
        getChart(modeA, storedIdA, customA),
        getChart(modeB, storedIdB, customB),
      ]);

      if (!chartA || !chartB) {
        setError("Could not compute one or both charts");
        return;
      }

      setNamesUsed({ a: chartA.name, b: chartB.name });

      const r = await toolsApi.kundaliMilan(chartA.chart, chartB.chart);
      setResult(r);

      // Optionally save custom profiles to vault
      if (modeA === "custom" && customA.addToVault && customA.resolvedLat !== null) {
        try {
          const p = await profilesApi.create({
            name: customA.name || "Person A",
            birth_date: customA.birthDate,
            birth_time: customA.birthTime || undefined,
            place_name: customA.resolvedPlace,
            lat: customA.resolvedLat,
            lng: customA.resolvedLng!,
            timezone: customA.resolvedTz,
          });
          onProfileAdded?.(p);
        } catch {
          /* silent */
        }
      }
      if (modeB === "custom" && customB.addToVault && customB.resolvedLat !== null) {
        try {
          const p = await profilesApi.create({
            name: customB.name || "Person B",
            birth_date: customB.birthDate,
            birth_time: customB.birthTime || undefined,
            place_name: customB.resolvedPlace,
            lat: customB.resolvedLat,
            lng: customB.resolvedLng!,
            timezone: customB.resolvedTz,
          });
          onProfileAdded?.(p);
        } catch {
          /* silent */
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Comparison failed");
    } finally {
      setLoading(false);
    }
  };

  const handleOpenChange = (o: boolean) => {
    if (!o) {
      setResult(null);
      setError("");
      setCustomA(emptyCustom());
      setCustomB(emptyCustom());
      setModeA(initialBoyId ? "stored" : "stored");
      setModeB("stored");
    }
    onOpenChange(o);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className={`glass-panel wobbly-border max-h-[90vh] overflow-y-auto transition-all duration-300 ${
          result ? "max-w-5xl" : "max-w-2xl"
        }`}
      >
        <DialogHeader>
          <DialogTitle className="font-headline-md text-xl text-primary">
            Kundali{" "}
            <span className="font-annotation-sm text-2xl text-solar-gold">
              Milan
            </span>
          </DialogTitle>
          {!result && (
            <p className="font-body-md text-sm text-on-surface-variant mt-1">
              Select two people from your vault or enter custom birth details to
              compute Ashtakoot compatibility.
            </p>
          )}
        </DialogHeader>

        <div
          className={`mt-4 transition-all duration-300 ${
            result
              ? "bg-surface-container/20 p-4 wobbly-border-sm rounded-xl border border-outline/10 flex flex-wrap items-end gap-4"
              : "bg-surface-container-low/40 p-6 rounded-xl wobbly-border-sm border border-outline/10"
          }`}
        >
          <div
            className={`${
              result
                ? "flex flex-wrap items-end gap-4 flex-1"
                : "grid grid-cols-1 md:grid-cols-2 gap-6"
            }`}
          >
            {/* ── Person A ─────────────────────── */}
            <PersonSlot
              label="Person A"
              labelColor="text-sky-400"
              mode={modeA}
              onModeChange={setModeA}
              storedId={storedIdA}
              onStoredIdChange={setStoredIdA}
              custom={customA}
              onCustomChange={setCustomA}
              computable={computable}
              resolving={resolvingA}
              onResolve={() =>
                resolvePlace("a", customA, setCustomA, setResolvingA)
              }
              compact={!!result}
            />

            {/* ── Person B ─────────────────────── */}
            <PersonSlot
              label="Person B"
              labelColor="text-rose-400"
              mode={modeB}
              onModeChange={setModeB}
              storedId={storedIdB}
              onStoredIdChange={setStoredIdB}
              custom={customB}
              onCustomChange={setCustomB}
              computable={computable}
              resolving={resolvingB}
              onResolve={() =>
                resolvePlace("b", customB, setCustomB, setResolvingB)
              }
              compact={!!result}
            />
          </div>

          <div
            className={`${
              result
                ? "flex-none pb-0.5"
                : "flex justify-end gap-2 mt-6"
            }`}
          >
            <button
              onClick={handleCompare}
              disabled={loading}
              className={`btn-primary wobbly-border-sm font-nav-label text-[11px] uppercase tracking-widest disabled:opacity-50 shadow-md ${
                result ? "px-6 py-2.5 h-[40px]" : "px-8 py-3"
              }`}
            >
              {loading
                ? "Computing…"
                : result
                ? "Recompute"
                : "Compute Milan"}
            </button>
          </div>
        </div>

        {error && (
          <p className="text-rose-400 text-sm font-body-md mt-3">{error}</p>
        )}

        {result && (
          <div className="mt-3 w-full animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div className="flex items-center justify-center gap-2 mb-4">
              <span className="px-3 py-1 wobbly-border-sm bg-sky-500/10 text-sky-300 font-nav-label text-[14px] uppercase tracking-widest">
                {namesUsed.a}
              </span>
              <span className="font-annotation-sm text-lg text-solar-gold">
                ×
              </span>
              <span className="px-3 py-1 wobbly-border-sm bg-rose-500/10 text-rose-300 font-nav-label text-[14px] uppercase tracking-widest">
                {namesUsed.b}
              </span>
            </div>
            <KundaliMilanCard data={result} fullWidth />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

/* ── Reusable person slot ──────────────────────────────────── */

function PersonSlot({
  label,
  labelColor,
  mode,
  onModeChange,
  storedId,
  onStoredIdChange,
  custom,
  onCustomChange,
  computable,
  resolving,
  onResolve,
  compact,
}: {
  label: string;
  labelColor: string;
  mode: SourceMode;
  onModeChange: (m: SourceMode) => void;
  storedId: string | undefined;
  onStoredIdChange: (id: string) => void;
  custom: CustomInput;
  onCustomChange: (c: CustomInput) => void;
  computable: BirthProfile[];
  resolving: boolean;
  onResolve: () => void;
  compact: boolean;
}) {
  if (compact) {
    // Collapsed inline view when results are showing
    const displayName =
      mode === "stored"
        ? computable.find((p) => p.id === storedId)?.name || "—"
        : custom.name || "Custom";
    return (
      <div className="w-full sm:w-[260px]">
        <div
          className={`font-nav-label text-[10px] uppercase tracking-widest ${labelColor} mb-1`}
        >
          {label}
        </div>
        <Select
          value={mode === "stored" ? storedId : "__custom__"}
          onValueChange={(v) => {
            if (v === "__custom__") {
              onModeChange("custom");
            } else {
              onModeChange("stored");
              onStoredIdChange(v);
            }
          }}
        >
          <SelectTrigger className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10">
            <SelectValue placeholder={displayName} />
          </SelectTrigger>
          <SelectContent className="bg-surface-container-lowest border-outline/30">
            {computable.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name} ({p.relationship || "—"})
              </SelectItem>
            ))}
            <SelectItem value="__custom__">✎ Custom Input</SelectItem>
          </SelectContent>
        </Select>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div
          className={`font-nav-label text-xs uppercase tracking-widest ${labelColor}`}
        >
          {label}
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => onModeChange("stored")}
            className={`px-2.5 py-1 wobbly-border-sm font-nav-label text-[9px] uppercase tracking-widest transition-colors ${
              mode === "stored"
                ? "bg-solar-gold/20 text-solar-gold border border-solar-gold/40"
                : "bg-surface-container text-on-surface-variant border border-outline/20 hover:text-primary"
            }`}
          >
            From Vault
          </button>
          <button
            type="button"
            onClick={() => onModeChange("custom")}
            className={`px-2.5 py-1 wobbly-border-sm font-nav-label text-[9px] uppercase tracking-widest transition-colors ${
              mode === "custom"
                ? "bg-solar-gold/20 text-solar-gold border border-solar-gold/40"
                : "bg-surface-container text-on-surface-variant border border-outline/20 hover:text-primary"
            }`}
          >
            Custom
          </button>
        </div>
      </div>

      {mode === "stored" ? (
        <Select value={storedId} onValueChange={onStoredIdChange}>
          <SelectTrigger className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10">
            <SelectValue placeholder="Select profile…" />
          </SelectTrigger>
          <SelectContent className="bg-surface-container-lowest border-outline/30">
            {computable.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name} ({p.relationship || "—"})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      ) : (
        <div className="space-y-2.5 bg-surface-container/30 p-3 wobbly-border-sm border border-outline/10">
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1">
              <Label className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
                Name
              </Label>
              <Input
                value={custom.name}
                onChange={(e) =>
                  onCustomChange({ ...custom, name: e.target.value })
                }
                placeholder="Person name"
                className="wobbly-border-sm bg-surface-container-low border-outline/20 font-body-md h-9 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
                Birth Date
              </Label>
              <Input
                type="date"
                value={custom.birthDate}
                onChange={(e) =>
                  onCustomChange({ ...custom, birthDate: e.target.value })
                }
                className="wobbly-border-sm bg-surface-container-low border-outline/20 font-body-md h-9 text-sm"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-2">
            <div className="space-y-1">
              <Label className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
                Birth Time
              </Label>
              <Input
                type="time"
                value={custom.birthTime}
                onChange={(e) =>
                  onCustomChange({ ...custom, birthTime: e.target.value })
                }
                className="wobbly-border-sm bg-surface-container-low border-outline/20 font-body-md h-9 text-sm"
              />
            </div>
            <div className="space-y-1">
              <Label className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
                Birth Place
              </Label>
              <div className="flex gap-1 relative">
                <Input
                  value={custom.placeName}
                  onChange={(e) =>
                    onCustomChange({
                      ...custom,
                      placeName: e.target.value,
                      resolvedLat: null,
                      resolvedLng: null,
                      resolvedTz: "",
                      resolvedPlace: "",
                    })
                  }
                  placeholder="City, country"
                  className="wobbly-border-sm bg-surface-container-low border-outline/20 font-body-md h-9 text-sm pr-16"
                />
                <button
                  type="button"
                  onClick={onResolve}
                  disabled={resolving || !custom.placeName.trim()}
                  className="absolute right-0.5 top-0.5 bottom-0.5 btn-ghost wobbly-border-sm px-2 font-nav-label text-[8px] uppercase tracking-widest text-solar-gold bg-surface-container-highest/30 hover:bg-surface-container-highest/60 disabled:opacity-40"
                >
                  {resolving ? "…" : "Resolve"}
                </button>
              </div>
            </div>
          </div>

          {custom.resolvedPlace && (
            <div className="text-[11px] font-body-md text-emerald-400 px-2 py-1 bg-emerald-500/10 wobbly-border-sm">
              ✓ {custom.resolvedPlace} · {custom.resolvedTz}
            </div>
          )}

          <label className="flex items-center gap-2 cursor-pointer mt-1">
            <input
              type="checkbox"
              checked={custom.addToVault}
              onChange={(e) =>
                onCustomChange({ ...custom, addToVault: e.target.checked })
              }
              className="w-3.5 h-3.5 rounded-sm accent-solar-gold"
            />
            <span className="font-body-md text-[11px] text-on-surface-variant">
              Also add this person to Family Vault
            </span>
          </label>
        </div>
      )}
    </div>
  );
}
