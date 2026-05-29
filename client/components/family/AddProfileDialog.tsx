"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { profilesApi, toolsApi, type BirthProfile } from "@/lib/api";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: (profile: BirthProfile) => void;
}

export default function AddProfileDialog({
  open,
  onOpenChange,
  onCreated,
}: Props) {
  const [name, setName] = useState("");
  const [relationship, setRelationship] = useState("self");
  const [birthDate, setBirthDate] = useState("");
  const [birthTime, setBirthTime] = useState("");
  const [placeName, setPlaceName] = useState("");
  const [resolved, setResolved] = useState<{
    lat: number;
    lng: number;
    timezone: string;
    canonical_name: string;
  } | null>(null);
  const [resolving, setResolving] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const reset = () => {
    setName("");
    setRelationship("self");
    setBirthDate("");
    setBirthTime("");
    setPlaceName("");
    setResolved(null);
    setError("");
  };

  const handleResolve = async () => {
    if (!placeName.trim()) return;
    setResolving(true);
    setError("");
    try {
      const r = await toolsApi.geocode(placeName.trim());
      setResolved(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resolve place");
      setResolved(null);
    } finally {
      setResolving(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolved) {
      setError("Resolve the place first.");
      return;
    }
    setSubmitting(true);
    setError("");
    try {
      const profile = await profilesApi.create({
        name,
        relationship,
        birth_date: birthDate,
        birth_time: birthTime || undefined,
        place_name: resolved.canonical_name,
        lat: resolved.lat,
        lng: resolved.lng,
        timezone: resolved.timezone,
      });
      onCreated(profile);
      reset();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add profile");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(o) => {
        if (!o) reset();
        onOpenChange(o);
      }}
    >
      <DialogContent className="glass-panel wobbly-border max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-headline-md text-xl text-primary">
            Add to Family Vault
          </DialogTitle>
          <DialogDescription className="font-body-md text-sm text-on-surface-variant">
            Add a person and we&apos;ll precompute their chart and dashas.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-2">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                Name
              </Label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Person name"
                required
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                Relationship
              </Label>
              <Select value={relationship} onValueChange={setRelationship}>
                <SelectTrigger className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-container-lowest border-outline/30">
                  <SelectItem value="self">Self</SelectItem>
                  <SelectItem value="spouse">Spouse</SelectItem>
                  <SelectItem value="partner">Partner</SelectItem>
                  <SelectItem value="parent">Parent</SelectItem>
                  <SelectItem value="child">Child</SelectItem>
                  <SelectItem value="sibling">Sibling</SelectItem>
                  <SelectItem value="friend">Friend</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                Birth Date
              </Label>
              <Input
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                required
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
            </div>
            <div className="space-y-1.5">
              <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                Birth Time
              </Label>
              <Input
                type="time"
                value={birthTime}
                onChange={(e) => setBirthTime(e.target.value)}
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Birth Place
            </Label>
            <div className="flex gap-2">
              <Input
                value={placeName}
                onChange={(e) => {
                  setPlaceName(e.target.value);
                  setResolved(null);
                }}
                placeholder="City, country"
                required
                className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
              />
              <button
                type="button"
                onClick={handleResolve}
                disabled={resolving || !placeName.trim()}
                className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-widest disabled:opacity-50"
              >
                {resolving ? "…" : "Resolve"}
              </button>
            </div>
            {resolved && (
              <div className="text-[11px] font-body-md text-emerald-400 px-2 py-1 bg-emerald-500/10 wobbly-border-sm">
                ✓ {resolved.canonical_name} · {resolved.timezone}
              </div>
            )}
          </div>

          {error && (
            <p className="text-rose-400 text-sm font-body-md">{error}</p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="btn-ghost wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !resolved}
              className="btn-primary wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest disabled:opacity-50"
            >
              {submitting ? "Adding…" : "Add Profile"}
            </button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
