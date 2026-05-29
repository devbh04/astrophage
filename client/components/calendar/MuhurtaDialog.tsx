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
      <DialogContent className="glass-panel wobbly-border max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-headline-md text-xl text-primary">
            Find Muhurta
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-3 mt-2">
          <div className="space-y-1.5">
            <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Purpose
            </Label>
            <Select value={purpose} onValueChange={setPurpose}>
              <SelectTrigger className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md">
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

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                Start
              </Label>
              <Input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                End
              </Label>
              <Input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Place (optional — defaults to current)
            </Label>
            <div className="flex gap-2">
              <Input
                value={placeQuery}
                onChange={(e) => {
                  setPlaceQuery(e.target.value);
                  setResolved(null);
                }}
                placeholder="City, country"
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
              <button
                type="button"
                onClick={resolvePlace}
                className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-widest"
              >
                Resolve
              </button>
            </div>
            {resolved && (
              <div className="text-[11px] text-emerald-400">
                ✓ {resolved.name} · {resolved.timezone}
              </div>
            )}
          </div>

          {error && <p className="text-rose-400 text-sm font-body-md">{error}</p>}

          <div className="flex justify-end gap-2 pt-2">
            <button
              onClick={handleFind}
              disabled={loading}
              className="btn-primary wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest disabled:opacity-50"
            >
              {loading ? "Searching…" : "Find windows"}
            </button>
          </div>

          {windows && (
            <div className="mt-4">
              <MuhurtaCard data={{ purpose, windows }} />
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
