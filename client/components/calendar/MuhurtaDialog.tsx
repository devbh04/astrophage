"use client";

import { useState } from "react";
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
import { toolsApi, type MuhurtaWindow } from "@/lib/api";
import MuhurtaCard from "@/components/cards/MuhurtaCard";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultLat: number;
  defaultLng: number;
  defaultTimezone: string;
}

const PURPOSES = [
  { value: "wedding", label: "Wedding" },
  { value: "travel", label: "Travel" },
  { value: "business_start", label: "Business Start" },
  { value: "griha_pravesh", label: "Griha Pravesh" },
  { value: "general", label: "General" },
];

export default function MuhurtaDialog({
  open,
  onOpenChange,
  defaultLat,
  defaultLng,
  defaultTimezone,
}: Props) {
  const [purpose, setPurpose] = useState("wedding");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [placeQuery, setPlaceQuery] = useState("");
  const [resolved, setResolved] = useState<{
    lat: number;
    lng: number;
    timezone: string;
    name: string;
  } | null>(null);
  const [windows, setWindows] = useState<MuhurtaWindow[] | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const resolvePlace = async () => {
    if (!placeQuery.trim()) return;
    try {
      const r = await toolsApi.geocode(placeQuery.trim());
      setResolved({
        lat: r.lat,
        lng: r.lng,
        timezone: r.timezone,
        name: r.canonical_name,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Geocode failed");
    }
  };

  const handleFind = async () => {
    setError("");
    setWindows(null);
    if (!startDate || !endDate) {
      setError("Pick both dates");
      return;
    }
    const lat = resolved?.lat ?? defaultLat;
    const lng = resolved?.lng ?? defaultLng;
    const tz = resolved?.timezone ?? defaultTimezone;
    setLoading(true);
    try {
      const r = await toolsApi.muhurta({
        purpose,
        start_date: startDate,
        end_date: endDate,
        lat,
        lng,
        timezone: tz,
      });
      setWindows(r.windows);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Muhurta failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className={`glass-panel wobbly-border max-h-[90vh] overflow-y-auto transition-all duration-300 ${windows ? "max-w-5xl" : "max-w-xl"}`}>
        <DialogHeader>
          <DialogTitle className="font-headline-md text-xl text-primary">
            Find Muhurta
          </DialogTitle>
        </DialogHeader>

        <div className={`mt-4 transition-all duration-300 ${windows ? "flex flex-wrap items-end gap-4 bg-surface-container/20 p-4 wobbly-border-sm rounded-xl border border-outline/10" : "bg-surface-container-low/40 p-6 rounded-xl wobbly-border-sm border border-outline/10 space-y-5"}`}>
          {!windows && (
            <div className="text-sm font-body-md text-on-surface-variant/80 border-b border-outline/10 pb-4">
              Specify your event details below to calculate the most favorable and inauspicious time windows.
            </div>
          )}

          <div className={`space-y-1.5 ${windows ? "flex-[1] min-w-[120px]" : ""}`}>
            <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
              Purpose
            </Label>
            <Select value={purpose} onValueChange={setPurpose}>
              <SelectTrigger className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-surface-container-lowest border-outline/30">
                {PURPOSES.map((p) => (
                  <SelectItem key={p.value} value={p.value}>
                    {p.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {windows ? (
            <>
              <div className="space-y-1.5 flex-[1] min-w-[130px]">
                <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
                  Start Date
                </Label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10"
                />
              </div>
              <div className="space-y-1.5 flex-[1] min-w-[130px]">
                <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
                  End Date
                </Label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10"
                />
              </div>
            </>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
                  Start Date
                </Label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
                  End Date
                </Label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10"
                />
              </div>
            </div>
          )}

          <div className={`space-y-1.5 ${windows ? "flex-[1.5] min-w-[200px]" : ""}`}>
            <div className="flex items-center justify-between">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-primary/80">
                Location
              </Label>
              {!windows && (
                <span className="font-body-md text-[10px] text-on-surface-variant/60 italic">Defaults to profile</span>
              )}
            </div>
            <div className="flex gap-2 relative">
              <Input
                value={placeQuery}
                onChange={(e) => {
                  setPlaceQuery(e.target.value);
                  setResolved(null);
                }}
                placeholder="e.g. Mumbai, India"
                className="wobbly-border-sm bg-surface-container border-outline/20 font-body-md shadow-sm h-10 pr-20"
              />
              <button
                type="button"
                onClick={resolvePlace}
                className="absolute right-1 top-1 bottom-1 btn-ghost wobbly-border-sm px-3 font-nav-label text-[9px] uppercase tracking-widest text-solar-gold bg-surface-container-highest/30 hover:bg-surface-container-highest/60"
              >
                Resolve
              </button>
            </div>
            {resolved && (
              <div className="text-[11px] text-emerald-400 font-body-md mt-1 absolute">
                ✓ {resolved.name}
              </div>
            )}
          </div>

          <div className={`${windows ? "flex-none pt-6" : "flex justify-end gap-2 pt-4"}`}>
            <button
              onClick={handleFind}
              disabled={loading}
              className={`btn-primary wobbly-border-sm font-nav-label text-[11px] uppercase tracking-widest disabled:opacity-50 shadow-md ${windows ? "px-6 py-2.5 h-[40px]" : "px-8 py-3"}`}
            >
              {loading ? "Searching…" : windows ? "Update" : "Calculate Muhurta"}
            </button>
          </div>
        </div>

        {error && <p className="text-rose-400 text-sm font-body-md mt-2">{error}</p>}

        {windows && (
          <div className="mt-6 w-full animate-in fade-in slide-in-from-bottom-2 duration-500">
            <MuhurtaCard data={{ purpose, windows }} fullWidth />
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
