"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import { Menu, History } from "lucide-react";
import { useAppStore } from "@/lib/store";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import ConversationDrawer from "./ConversationDrawer";
import { authApi } from "@/lib/api";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "ta", label: "தமிழ்" },
  { code: "kn", label: "ಕನ್ನಡ" },
];

const PAGE_TITLES: Record<string, string> = {
  "/chat": "Chat",
  "/chart": "Birth Chart",
  "/family": "Family Vault",
  "/calendar": "Calendar",
  "/settings": "Settings",
};

export default function Topbar() {
  const pathname = usePathname();
  const { language, setLanguage, setUser, toggleSidebar } = useAppStore();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const pageTitle =
    Object.entries(PAGE_TITLES).find(([path]) =>
      pathname.startsWith(path)
    )?.[1] || "Astrophage";

  const handleLanguage = async (lang: string) => {
    setLanguage(lang);
    try {
      const u = await authApi.updatePreferences({ default_language: lang });
      setUser(u);
    } catch {
      /* offline ok */
    }
  };

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between px-6 py-4 border-b border-dashed border-outline/20 bg-background/80 backdrop-blur-md">
      <div className="flex items-center gap-4">
        <button
          onClick={toggleSidebar}
          className="hidden p-2 hover:bg-surface-container rounded-md text-on-surface-variant"
        >
          <Menu size={20} />
        </button>
        <h1 className="font-headline-md text-xl text-primary">{pageTitle}</h1>
      </div>

      <div className="flex items-center gap-2">
        {pathname.startsWith("/chat") && (
          <button
            onClick={() => setDrawerOpen(true)}
            className="p-2 rounded-md hover:bg-surface-container text-on-surface-variant hover:text-solar-gold"
            aria-label="Conversation history"
          >
            <History size={18} />
          </button>
        )}

        <Select value={language} onValueChange={handleLanguage}>
          <SelectTrigger className="w-[120px] wobbly-border-sm bg-surface-container-low border-outline/30 font-nav-label text-xs uppercase tracking-wider">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-surface-container-lowest border-outline/30">
            {LANGUAGES.map((lang) => (
              <SelectItem
                key={lang.code}
                value={lang.code}
                className="font-body-md text-sm"
              >
                {lang.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <ConversationDrawer open={drawerOpen} onOpenChange={setDrawerOpen} />
    </header>
  );
}
