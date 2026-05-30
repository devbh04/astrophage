"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAppStore } from "@/lib/store";
import { authApi } from "@/lib/api";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import SelfBirthDetailsCard from "@/components/settings/SelfBirthDetailsCard";
import ResidenceCard from "@/components/settings/ResidenceCard";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "ta", label: "தமிழ்" },
  { code: "kn", label: "ಕನ್ನಡ" },
];

export default function SettingsPage() {
  const router = useRouter();
  const { user, setUser, language, setLanguage } = useAppStore();
  const [chartFormat, setChartFormat] = useState(
    user?.chart_format || "south_indian"
  );
  const [savedTick, setSavedTick] = useState(false);

  const persist = async (updates: {
    default_language?: string;
    chart_format?: string;
  }) => {
    try {
      const updated = await authApi.updatePreferences(updates);
      setUser(updated);
      setSavedTick(true);
      setTimeout(() => setSavedTick(false), 1500);
    } catch (err) {
      console.error(err);
    }
  };

  const handleLanguageChange = (lang: string) => {
    setLanguage(lang);
    void persist({ default_language: lang });
  };

  const handleChartFormatChange = (fmt: string) => {
    setChartFormat(fmt);
    void persist({ chart_format: fmt });
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
      setUser(null);
      router.push("/login");
    } catch (err) {
      console.error("Logout failed:", err);
    }
  };

  return (
    <div className="p-6 md:p-8 max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline-md text-2xl text-primary mb-2">
            Settings
          </h2>
          <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
            CONFIGURE YOUR COSMIC EXPERIENCE
          </p>
        </div>
        {savedTick && (
          <span className="font-nav-label text-[10px] uppercase tracking-widest text-emerald-400 px-3 py-1 bg-emerald-500/10 wobbly-border-sm">
            ✓ Saved
          </span>
        )}
      </div>

      <div className="space-y-8">
        <section className="glass-panel wobbly-border p-6">
          <h3 className="font-headline-md text-lg text-primary mb-4">Account</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-body-md text-on-surface-variant">Name</span>
              <span className="font-body-md text-primary">{user?.name}</span>
            </div>
            <Separator className="border-dashed border-outline/20" />
            <div className="flex justify-between items-center">
              <span className="font-body-md text-on-surface-variant">Email</span>
              <span className="font-body-md text-primary">{user?.email}</span>
            </div>
          </div>
        </section>

        <section className="glass-panel wobbly-border p-6">
          <h3 className="font-headline-md text-lg text-primary mb-4">
            Preferences
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <div>
                <p className="font-body-md text-primary">Language</p>
                <p className="font-body-md text-xs text-on-surface-variant">
                  Agent responses and UI language
                </p>
              </div>
              <Select value={language} onValueChange={handleLanguageChange}>
                <SelectTrigger className="w-[140px] wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-container-lowest border-outline/30">
                  {LANGUAGES.map((lang) => (
                    <SelectItem key={lang.code} value={lang.code}>
                      {lang.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <Separator className="border-dashed border-outline/20" />

            <div className="flex justify-between items-center">
              <div>
                <p className="font-body-md text-primary">Chart Format</p>
                <p className="font-body-md text-xs text-on-surface-variant">
                  South Indian (square) or North Indian (diamond)
                </p>
              </div>
              <Select
                value={chartFormat}
                onValueChange={handleChartFormatChange}
              >
                <SelectTrigger className="w-[160px] wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-sm">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-surface-container-lowest border-outline/30">
                  <SelectItem value="south_indian">South Indian</SelectItem>
                  <SelectItem value="north_indian">North Indian</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </section>

        <SelfBirthDetailsCard />

        <ResidenceCard />

        <section>
          <button
            onClick={handleLogout}
            className="btn-ghost wobbly-border w-full py-4 font-nav-label text-nav-label uppercase tracking-[0.15em] hover:border-error hover:text-error"
          >
            SIGN OUT
          </button>
        </section>
      </div>
    </div>
  );
}
