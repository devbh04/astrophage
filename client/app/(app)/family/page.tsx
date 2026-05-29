"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, Eye, GitCompare, Trash2 } from "lucide-react";
import { profilesApi, type BirthProfile } from "@/lib/api";
import { useAppStore } from "@/lib/store";
import AddProfileDialog from "@/components/family/AddProfileDialog";
import CompareDialog from "@/components/family/CompareDialog";

export default function FamilyPage() {
  const { profiles, setProfiles, addProfile, removeProfile } = useAppStore();
  const [loading, setLoading] = useState(true);
  const [addOpen, setAddOpen] = useState(false);
  const [compareOpen, setCompareOpen] = useState(false);
  const [compareSeed, setCompareSeed] = useState<string | undefined>();

  useEffect(() => {
    profilesApi
      .list()
      .then((data) => setProfiles(data))
      .catch((err) => console.error("Failed to load profiles:", err))
      .finally(() => setLoading(false));
  }, [setProfiles]);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this profile?")) return;
    try {
      await profilesApi.delete(id);
      removeProfile(id);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Delete failed");
    }
  };

  const handleCreated = (p: BirthProfile) => {
    addProfile(p);
  };

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
        <div className="flex gap-2">
          {profiles.length >= 2 && (
            <button
              onClick={() => {
                setCompareSeed(undefined);
                setCompareOpen(true);
              }}
              className="btn-ghost wobbly-border-sm px-4 py-3 font-nav-label text-xs uppercase tracking-widest flex items-center gap-2"
            >
              <GitCompare size={14} />
              COMPARE
            </button>
          )}
          <button
            onClick={() => setAddOpen(true)}
            className="btn-primary wobbly-border-sm px-6 py-3 font-nav-label text-xs uppercase tracking-widest flex items-center gap-2"
          >
            <Plus size={16} />
            ADD MEMBER
          </button>
        </div>
      </div>

      {profiles.length === 0 ? (
        <button
          onClick={() => setAddOpen(true)}
          className="w-full glass-panel wobbly-border p-12 text-center hover:bg-surface-container/40 transition-colors"
        >
          <span className="material-symbols-outlined text-6xl text-outline-variant mb-4">
            group_add
          </span>
          <p className="font-annotation-sm text-lg text-solar-gold mb-2">
            Your vault is empty
          </p>
          <p className="font-body-md text-sm text-on-surface-variant">
            Click here to add your first profile.
          </p>
        </button>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profiles.map((profile) => {
            const moonSign =
              (profile.computed_chart as { moon_sign?: string } | undefined)
                ?.moon_sign || "—";
            const sunSign =
              (profile.computed_chart as { sun_sign?: string } | undefined)
                ?.sun_sign || "—";
            return (
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
                    <div className="flex flex-col items-end gap-1">
                      <span className="px-2 py-0.5 text-[9px] font-nav-label uppercase tracking-wider bg-surface-container wobbly-border-sm text-solar-gold">
                        ☉ {sunSign}
                      </span>
                      <span className="px-2 py-0.5 text-[9px] font-nav-label uppercase tracking-wider bg-surface-container wobbly-border-sm text-sky-300">
                        ☽ {moonSign}
                      </span>
                    </div>
                  )}
                </div>

                <p className="font-body-md text-sm text-on-surface-variant mb-1">
                  Born: {profile.birth_date}
                  {profile.birth_time ? ` · ${profile.birth_time}` : ""}
                </p>
                {profile.place_name && (
                  <p className="font-body-md text-xs text-on-surface-variant truncate">
                    📍 {profile.place_name}
                  </p>
                )}

                <div className="flex flex-wrap gap-2 mt-4">
                  <Link
                    href={`/family/${profile.id}`}
                    className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-wider flex items-center gap-1"
                  >
                    <Eye size={12} />
                    VIEW
                  </Link>
                  {profile.computed_chart && (
                    <button
                      onClick={() => {
                        setCompareSeed(profile.id);
                        setCompareOpen(true);
                      }}
                      className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-wider flex items-center gap-1"
                    >
                      <GitCompare size={12} />
                      COMPARE
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(profile.id)}
                    className="btn-ghost wobbly-border-sm px-3 py-2 font-nav-label text-[10px] uppercase tracking-wider flex items-center gap-1 hover:text-rose-400 ml-auto"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <AddProfileDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        onCreated={handleCreated}
      />
      <CompareDialog
        open={compareOpen}
        onOpenChange={setCompareOpen}
        profiles={profiles}
        initialBoyId={compareSeed}
      />
    </div>
  );
}
