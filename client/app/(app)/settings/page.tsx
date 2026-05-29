"use client";

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
      <div className="mb-8">
        <h2 className="font-headline-md text-2xl text-primary mb-2">
          Settings
        </h2>
        <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
          CONFIGURE YOUR COSMIC EXPERIENCE
        </p>
      </div>

      <div className="space-y-8">
        {/* Account */}
        <section className="glass-panel wobbly-border p-6">
          <h3 className="font-headline-md text-lg text-primary mb-4">
            Account
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="font-body-md text-on-surface-variant">
                Name
              </span>
              <span className="font-body-md text-primary">
                {user?.name}
              </span>
            </div>
            <Separator className="border-dashed border-outline/20" />
            <div className="flex justify-between items-center">
              <span className="font-body-md text-on-surface-variant">
                Email
              </span>
              <span className="font-body-md text-primary">
                {user?.email}
              </span>
            </div>
          </div>
        </section>

        {/* Preferences */}
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
              <Select value={language} onValueChange={setLanguage}>
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
              <Select defaultValue="south_indian">
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

        {/* Actions */}
        <section className="space-y-4">
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
