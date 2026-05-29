"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { authApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";

const LANGUAGES = [
  { code: "en", label: "English" },
  { code: "hi", label: "हिन्दी" },
  { code: "mr", label: "मराठी" },
  { code: "gu", label: "ગુજરાતી" },
  { code: "ta", label: "தமிழ்" },
  { code: "kn", label: "ಕನ್ನಡ" },
];

export default function RegisterPage() {
  const router = useRouter();
  const setUser = useAppStore((s) => s.setUser);

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [language, setLanguage] = useState("en");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await authApi.register({
        email,
        password,
        name,
        default_language: language,
      });
      setUser(user);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel wobbly-border p-8 md:p-12 shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)]">
      <div className="tape-strip-right" />

      <div className="text-center mb-8">
        <h1 className="font-annotation-sm text-3xl text-solar-gold mb-2">
          Begin Your Journey
        </h1>
        <p className="font-headline-md text-headline-md text-primary">
          Create Account
        </p>
        <p className="font-body-md text-sm text-on-surface-variant mt-2">
          Decode your destiny with cosmic precision
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <Label className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant">
            Name
          </Label>
          <Input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant focus:border-solar-gold"
          />
        </div>

        <div className="space-y-2">
          <Label className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant">
            Email
          </Label>
          <Input
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant focus:border-solar-gold"
          />
        </div>

        <div className="space-y-2">
          <Label className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant">
            Password
          </Label>
          <Input
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant focus:border-solar-gold"
          />
        </div>

        <div className="space-y-2">
          <Label className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant">
            Preferred Language
          </Label>
          <Select value={language} onValueChange={setLanguage}>
            <SelectTrigger className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface">
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

        {error && (
          <p className="text-error text-sm font-body-md">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary wobbly-border w-full py-4 font-nav-label text-nav-label uppercase tracking-[0.15em] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "CHARTING YOUR STARS..." : "CREATE ACCOUNT"}
        </button>
      </form>

      <div className="mt-8 text-center">
        <p className="font-body-md text-sm text-on-surface-variant">
          Already have an account?{" "}
          <Link
            href="/login"
            className="text-solar-gold hover:underline font-nav-label uppercase tracking-wider text-xs"
          >
            SIGN IN
          </Link>
        </p>
      </div>
    </div>
  );
}
