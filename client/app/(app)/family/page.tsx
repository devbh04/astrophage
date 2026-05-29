"use client";

import { useEffect, useState } from "react";
import { Plus, Eye, GitCompare } from "lucide-react";
import { profilesApi, type BirthProfile } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function FamilyPage() {
  const { profiles, setProfiles } = useAppStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadProfiles = async () => {
      try {
        const data = await profilesApi.list();
        setProfiles(data);
      } catch (err) {
        console.error("Failed to load profiles:", err);
      } finally {
        setLoading(false);
      }
    };
    loadProfiles();
  }, [setProfiles]);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[60vh]">
        <div className="w-3 h-3 rounded-full bg-solar-gold animate-pulse" />
      </div>
    );
  }

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline-md text-2xl text-primary mb-2">
            The Family{" "}
            <span className="font-annotation-sm text-3xl text-solar-gold">
              Vault
            </span>
          </h2>
          <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
            SECURE KINSHIP DATA MATRIX
          </p>
        </div>
        <button className="btn-primary wobbly-border-sm px-6 py-3 font-nav-label text-xs uppercase tracking-widest flex items-center gap-2">
          <Plus size={16} />
          ADD MEMBER
        </button>
      </div>

      {profiles.length === 0 ? (
        <div className="glass-panel wobbly-border p-12 text-center">
          <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
            group_add
          </span>
          <p className="font-annotation-sm text-lg text-solar-gold mb-2">
            Your vault is empty
          </p>
          <p className="font-body-md text-sm text-on-surface-variant">
            Add family members to compare charts, check compatibility, and
            track shared cosmic patterns.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profiles.map((profile) => (
            <div
              key={profile.id}
              className="glass-panel wobbly-border p-6 relative group hover:shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)] transition-shadow"
            >
              <div className="tape-strip" />
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="font-headline-md text-lg text-primary">
                    {profile.name}
                  </h3>
                  {profile.relationship && (
                    <span className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                      {profile.relationship}
                    </span>
                  )}
                </div>
                {profile.computed_chart && (
                  <span className="px-2 py-1 text-[10px] font-nav-label uppercase tracking-wider bg-surface-container wobbly-border-sm text-solar-gold">
                    {(profile.computed_chart as Record<string, string>)
                      ?.moon_sign || "—"}
                  </span>
                )}
              </div>

              <p className="font-body-md text-sm text-on-surface-variant mb-1">
                Born: {profile.birth_date}
              </p>
              {profile.place_name && (
                <p className="font-body-md text-sm text-on-surface-variant mb-4">
                  📍 {profile.place_name}
                </p>
              )}

              <div className="flex gap-2 mt-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-wider flex items-center gap-1">
                  <Eye size={12} />
                  CHART
                </button>
                <button className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-wider flex items-center gap-1">
                  <GitCompare size={12} />
                  COMPARE
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
