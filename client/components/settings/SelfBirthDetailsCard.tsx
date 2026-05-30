"use client";

import { useEffect, useMemo, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  profilesApi,
  toolsApi,
  type BirthProfile,
} from "@/lib/api";
import { useAppStore } from "@/lib/store";

/**
 * Self birth details card for /settings.
 *
 * Reads/writes the user's ``relationship = "self"`` row in the
 * ``birth_profiles`` table. We keep it in the family vault on purpose so
 * the profile id can be passed to tools that already understand
 * ``natal_chart``-shaped inputs.
 *
 * We do NOT recompute the chart inside this card — that's the family
 * detail page's job (the Recompute button there does the same work). New
 * profiles get an automatic chart precompute on the server side.
 */
export default function SelfBirthDetailsCard() {
  const { profiles, addProfile, setProfiles } = useAppStore();
  const selfProfile = useMemo<BirthProfile | undefined>(
    () => profiles.find((p) => p.relationship === "self"),
    [profiles]
  );

  const [name, setName] = useState("");
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
  const [saving, setSaving] = useState(false);
  const [savedTick, setSavedTick] = useState(false);
  const [error, setError] = useState("");

  // Hydrate the form from the current self profile on mount / change.
  useEffect(() => {
    if (selfProfile) {
      setName(selfProfile.name);
      setBirthDate(selfProfile.birth_date || "");
      setBirthTime(selfProfile.birth_time || "");
      setPlaceName(selfProfile.place_name || "");
      setResolved({
        lat: selfProfile.lat,
        lng: selfProfile.lng,
        timezone: selfProfile.timezone,
        canonical_name: selfProfile.place_name || "",
      });
    }
  }, [selfProfile]);

  const handleResolve = async () => {
    if (!placeName.trim()) return;
    setResolving(true);
    setError("");
    try {
      const r = await toolsApi.geocode(placeName.trim());
      setResolved(r);
      setPlaceName(r.canonical_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not resolve place");
      setResolved(null);
    } finally {
      setResolving(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !birthDate || !resolved) {
      setError("Provide a name, birth date, and resolved birth place.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (selfProfile) {
        const updated = await profilesApi.patch(selfProfile.id, {
          name,
          birth_date: birthDate,
          birth_time: birthTime || undefined,
          place_name: resolved.canonical_name,
          lat: resolved.lat,
          lng: resolved.lng,
          timezone: resolved.timezone,
        });
        setProfiles(
          profiles.map((p) => (p.id === updated.id ? updated : p))
        );
      } else {
        const created = await profilesApi.create({
          name,
          relationship: "self",
          birth_date: birthDate,
          birth_time: birthTime || undefined,
          place_name: resolved.canonical_name,
          lat: resolved.lat,
          lng: resolved.lng,
          timezone: resolved.timezone,
        });
        addProfile(created);
      }
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <section className="glass-panel wobbly-border p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-headline-md text-lg text-primary">
          Your Birth Details
        </h3>
        {savedTick && (
          <span className="font-nav-label text-[10px] uppercase tracking-widest text-emerald-400 px-2 py-0.5 bg-emerald-500/10 wobbly-border-sm">
            ✓ Saved
          </span>
        )}
      </div>
      <p className="font-body-md text-xs text-on-surface-variant mb-4">
        Sent with every chat request so the agent can answer about you
        without re-asking. Stored as a ``relationship = self`` profile in
        the family vault.
      </p>

      <form onSubmit={handleSave} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
              Name
            </Label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Your name"
              required
              className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md"
            />
          </div>
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
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
          </div>
        </div>

        {resolved && (
          <div className="text-[11px] font-body-md text-emerald-400 px-2 py-1 bg-emerald-500/10 wobbly-border-sm w-fit">
            ✓ {resolved.canonical_name} · {resolved.timezone}
          </div>
        )}

        {error && (
          <p className="text-rose-400 text-sm font-body-md">{error}</p>
        )}

        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={saving || !resolved}
            className="btn-primary wobbly-border-sm px-4 py-2 font-nav-label text-[10px] uppercase tracking-widest disabled:opacity-50"
          >
            {saving ? "Saving…" : selfProfile ? "Update" : "Save"}
          </button>
        </div>
      </form>
    </section>
  );
}
