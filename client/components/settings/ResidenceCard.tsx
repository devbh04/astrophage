"use client";

import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi, toolsApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";

/**
 * Place-of-residence card for /settings.
 *
 * Stored on the ``users`` row, sent with every chat request, used by
 * tools that need the *current* location (today's panchang, current
 * sky, daily transits) when the user doesn't name a different place.
 */
export default function ResidenceCard() {
  const { user, setUser } = useAppStore();
  const [placeName, setPlaceName] = useState(user?.residence_place_name || "");
  const [resolved, setResolved] = useState<{
    lat: number;
    lng: number;
    timezone: string;
    canonical_name: string;
  } | null>(
    user?.residence_lat != null && user?.residence_lng != null && user?.residence_timezone
      ? {
          lat: user.residence_lat,
          lng: user.residence_lng,
          timezone: user.residence_timezone,
          canonical_name: user.residence_place_name || "",
        }
      : null
  );
  const [resolving, setResolving] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedTick, setSavedTick] = useState(false);
  const [error, setError] = useState("");

  // Re-sync from store when user object changes (login flow, refresh).
  useEffect(() => {
    if (user?.residence_place_name) {
      setPlaceName(user.residence_place_name);
      if (user.residence_lat != null && user.residence_lng != null && user.residence_timezone) {
        setResolved({
          lat: user.residence_lat,
          lng: user.residence_lng,
          timezone: user.residence_timezone,
          canonical_name: user.residence_place_name,
        });
      }
    }
  }, [user]);

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
    if (!resolved) {
      setError("Resolve the place first.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      const updated = await authApi.updatePreferences({
        residence_place_name: resolved.canonical_name,
        residence_lat: resolved.lat,
        residence_lng: resolved.lng,
        residence_timezone: resolved.timezone,
      });
      setUser(updated);
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
          Place of Residence
        </h3>
        {savedTick && (
          <span className="font-nav-label text-[10px] uppercase tracking-widest text-emerald-400 px-2 py-0.5 bg-emerald-500/10 wobbly-border-sm">
            ✓ Saved
          </span>
        )}
      </div>
      <p className="font-body-md text-xs text-on-surface-variant mb-4">
        Used as the default location for today&apos;s Panchang, transits,
        and current-sky tools when you don&apos;t mention a place.
      </p>

      <form onSubmit={handleSave} className="space-y-3">
        <div className="space-y-1.5">
          <Label className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
            Current City
          </Label>
          <div className="flex gap-2">
            <Input
              value={placeName}
              onChange={(e) => {
                setPlaceName(e.target.value);
                setResolved(null);
              }}
              placeholder="City, country"
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
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </section>
  );
}
