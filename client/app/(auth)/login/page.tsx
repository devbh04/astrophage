"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { authApi } from "@/lib/api";
import { useAppStore } from "@/lib/store";

export default function LoginPage() {
  const router = useRouter();
  const setUser = useAppStore((s) => s.setUser);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const user = await authApi.login({ email, password });
      setUser(user);
      router.push("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel wobbly-border p-8 md:p-12 shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)]">
      {/* Tape strip decoration */}
      <div className="tape-strip" />

      <div className="text-center mb-8">
        <h1 className="font-annotation-sm text-3xl text-solar-gold mb-2">
          Welcome Back
        </h1>
        <p className="font-headline-md text-headline-md text-primary">
          Sign In
        </p>
        <p className="font-body-md text-sm text-on-surface-variant mt-2">
          Continue your cosmic journey
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-2">
          <Label
            htmlFor="email"
            className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant"
          >
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="your@email.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant focus:border-solar-gold focus:ring-solar-gold/20"
          />
        </div>

        <div className="space-y-2">
          <Label
            htmlFor="password"
            className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant"
          >
            Password
          </Label>
          <Input
            id="password"
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="wobbly-border-sm bg-surface-container-low border-outline/30 font-body-md text-on-surface placeholder:text-outline-variant focus:border-solar-gold focus:ring-solar-gold/20"
          />
        </div>

        {error && (
          <p className="text-error text-sm font-body-md">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="btn-primary wobbly-border w-full py-4 font-nav-label text-nav-label uppercase tracking-[0.15em] disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? "ALIGNING STARS..." : "SIGN IN"}
        </button>
      </form>

      <div className="mt-8 text-center">
        <p className="font-body-md text-sm text-on-surface-variant">
          New to the cosmos?{" "}
          <Link
            href="/register"
            className="text-solar-gold hover:underline font-nav-label uppercase tracking-wider text-xs"
          >
            CREATE ACCOUNT
          </Link>
        </p>
      </div>
    </div>
  );
}
