"use client";

import { useEffect, useState, type ReactNode } from "react";
import { Sparkles } from "lucide-react";

const ANNOUNCE_HOLD_MS = 700;

interface Props {
  /** Name of the tool whose card is rendering — drives the headline. */
  cardType: string;
  /** Card body, already constructed by the caller. */
  children: ReactNode;
}

const HEADLINES: Record<string, string> = {
  birth_chart: "Here is your birth chart",
  dasha_timeline: "Here is your Dasha timeline",
  nakshatra: "Here is your Nakshatra",
  sade_sati: "Here is your Sade Sati reading",
  panchang: "Here is the Panchang",
  muhurta: "Here are your auspicious windows",
  daily_transits: "Here are today's transits",
  current_sky: "Here is the current sky",
  kundali_milan: "Here is your Kundali match",
};

function headlineFor(cardType: string): string {
  return HEADLINES[cardType] || `Here is ${cardType.replace(/_/g, " ")}`;
}

/**
 * Two-stage card entry for voice mode.
 *
 * Stage 1 (0 → ANNOUNCE_HOLD_MS): a small "Here is your X" pill fades in
 * from below to mirror what the assistant is saying out loud.
 * Stage 2 (after the hold): the actual card slides into place. The pill
 * fades out at the same time, leaving a clean card on the stack.
 *
 * The headline always sits visually *above* the card, and because the
 * parent renders newest-first, the most recent reading lands at the top
 * of the modal's card stack.
 */
export default function VoiceCardEntry({ cardType, children }: Props) {
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setRevealed(true), ANNOUNCE_HOLD_MS);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="flex flex-col items-center w-full gap-3">
      <div
        className={`flex items-center gap-2 px-3 py-1.5 wobbly-border-sm bg-surface-container-low/80 border border-solar-gold/40 transition-all duration-500 ${
          revealed ? "opacity-0 -translate-y-1" : "opacity-100"
        }`}
      >
        <Sparkles size={12} className="text-solar-gold" />
        <span className="font-annotation-sm text-sm text-solar-gold">
          {headlineFor(cardType)}
        </span>
      </div>
      <div
        className={`w-full transition-all duration-500 ${
          revealed
            ? "opacity-100 translate-y-0"
            : "opacity-0 translate-y-2 pointer-events-none"
        }`}
      >
        {children}
      </div>
    </div>
  );
}
