"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  Mic,
  MicOff,
  PhoneOff,
  Wrench,
  Loader2,
  Check,
  AlertTriangle,
} from "lucide-react";

import {
  connectVoiceSocket,
  type VoiceEvent,
  type VoiceSocket,
} from "@/lib/voice";
import {
  createPlayer,
  startMicCapture,
  type AudioPlayer,
  type MicCapture,
} from "@/lib/voice_audio";
import VoiceOrb from "./VoiceOrb";
import VoiceCardEntry from "./VoiceCardEntry";
import StructuredCard from "@/components/cards/StructuredCard";
import ChartSvgCard from "@/components/cards/ChartSvgCard";

interface Props {
  open: boolean;
  onClose: () => void;
}

interface ToolBadge {
  id: number;
  tool: string;
  status: "running" | "ok" | "error";
}

/**
 * One entry in the modal's vertical card stack. Either a structured card
 * (panchang, dasha, etc) or the SVG chart visual. They share a stack so
 * the newest reading — whatever its kind — is always at the top.
 */
type StackEntry =
  | {
      kind: "card";
      id: number;
      card_type: string;
      data: Record<string, unknown>;
    }
  | {
      kind: "chart_svg";
      id: number;
      svg: string;
    };

const TOOL_LABELS: Record<string, string> = {
  compute_birth_chart: "Birth chart",
  geocode_place: "Geocode place",
  compute_dasha_periods: "Dasha periods",
  compute_nakshatra_details: "Nakshatra",
  check_sade_sati: "Sade Sati",
  get_panchang: "Panchang",
  knowledge_lookup: "Knowledge lookup",
  kundali_milan: "Kundali Milan",
  render_chart_svg: "Birth chart",
  compute_muhurta: "Muhurta",
  get_daily_transits: "Daily transits",
  get_current_sky: "Current sky",
  get_family_profile: "Family profile",
};

function labelFor(name: string): string {
  return TOOL_LABELS[name] || name.replace(/_/g, " ");
}

export default function VoiceModal({ open, onClose }: Props) {
  const [phase, setPhase] = useState<"idle" | "connecting" | "ready" | "ended">(
    "idle"
  );
  const [error, setError] = useState<string | null>(null);
  const [muted, setMuted] = useState(false);
  const [tools, setTools] = useState<ToolBadge[]>([]);
  const [stack, setStack] = useState<StackEntry[]>([]);
  const [partialUserText, setPartialUserText] = useState("");
  const [partialAssistantText, setPartialAssistantText] = useState("");
  const [orbState, setOrbState] = useState<"user" | "assistant" | "idle">(
    "idle"
  );

  const socketRef = useRef<VoiceSocket | null>(null);
  const micRef = useRef<MicCapture | null>(null);
  const playerRef = useRef<AudioPlayer | null>(null);
  const idCounterRef = useRef(0);
  const lastAudioFromAssistantRef = useRef<number>(0);

  const nextId = () => {
    idCounterRef.current += 1;
    return idCounterRef.current;
  };

  // Drive the orb tint between user (mic loud) and assistant (audio
  // playing). We poll a couple of times a second; the orb canvas itself
  // runs at 60 fps off the analyser.
  useEffect(() => {
    if (phase !== "ready") {
      setOrbState("idle");
      return;
    }
    const id = setInterval(() => {
      const recentAssistant =
        Date.now() - lastAudioFromAssistantRef.current < 300;
      setOrbState(recentAssistant ? "assistant" : muted ? "idle" : "user");
    }, 120);
    return () => clearInterval(id);
  }, [phase, muted]);

  const handleEvent = useCallback((e: VoiceEvent) => {
    if (e.type === "ready") {
      setPhase("ready");
      return;
    }
    if (e.type === "tool_start") {
      setTools((prev) => [
        ...prev,
        { id: nextId(), tool: e.tool_name, status: "running" },
      ]);
      return;
    }
    if (e.type === "tool_end") {
      setTools((prev) => {
        const next = [...prev];
        for (let i = next.length - 1; i >= 0; i--) {
          if (next[i].tool === e.tool_name && next[i].status === "running") {
            next[i] = { ...next[i], status: e.ok === false ? "error" : "ok" };
            break;
          }
        }
        return next;
      });
      return;
    }
    if (e.type === "structured_card") {
      // Knowledge cards are dropped server-side, but defensively skip here too.
      if (e.card_type === "knowledge") return;
      setStack((prev) => [
        {
          kind: "card",
          id: nextId(),
          card_type: e.card_type,
          data: e.data || {},
        },
        ...prev,
      ]);
      return;
    }
    if (e.type === "chart_svg") {
      if (!e.svg || !e.svg.trim()) return;
      setStack((prev) => [
        { kind: "chart_svg", id: nextId(), svg: e.svg },
        ...prev,
      ]);
      return;
    }
    if (e.type === "input_transcription") {
      setPartialUserText((prev) => prev + e.text);
      return;
    }
    if (e.type === "output_transcription") {
      setPartialAssistantText((prev) => prev + e.text);
      return;
    }
    if (e.type === "turn_complete") {
      setPartialUserText("");
      setPartialAssistantText("");
      return;
    }
    if (e.type === "error") {
      setError(e.message);
      return;
    }
  }, []);

  const stop = useCallback(() => {
    setPhase("ended");
    try {
      socketRef.current?.stop();
    } catch {
      /* noop */
    }
    try {
      micRef.current?.stop();
    } catch {
      /* noop */
    }
    try {
      playerRef.current?.close();
    } catch {
      /* noop */
    }
    socketRef.current = null;
    micRef.current = null;
    playerRef.current = null;
  }, []);

  const handleClose = useCallback(() => {
    stop();
    onClose();
  }, [onClose, stop]);

  // Boot the voice session on open.
  //
  // React StrictMode in dev double-invokes effects: mount → cleanup →
  // mount again. Without a guard, two parallel WS sessions race each
  // other to /ws/voice and Gemini Live, often tearing down before the
  // first turn completes. We defer the actual init through a 60 ms
  // timer so a quick mount-unmount-remount cycle is a no-op on the
  // network.
  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    let initTimer: ReturnType<typeof setTimeout> | null = null;
    setError(null);
    setPhase("connecting");
    setTools([]);
    setStack([]);
    setPartialUserText("");
    setPartialAssistantText("");
    setMuted(false);

    const init = async () => {
      try {
        const player = createPlayer();
        if (cancelled) {
          player.close();
          return;
        }
        playerRef.current = player;

        const socket = connectVoiceSocket({
          onAudio: (chunk) => {
            lastAudioFromAssistantRef.current = Date.now();
            playerRef.current?.push(chunk);
          },
          onEvent: handleEvent,
          onClose: () => {
            if (!cancelled) setPhase("ended");
          },
        });
        if (cancelled) {
          socket.stop();
          return;
        }
        socketRef.current = socket;

        const mic = await startMicCapture((pcm) => {
          socketRef.current?.sendAudio(pcm);
        });
        if (cancelled) {
          mic.stop();
          return;
        }
        micRef.current = mic;
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Voice setup failed");
          setPhase("ended");
        }
      }
    };

    initTimer = setTimeout(() => {
      initTimer = null;
      void init();
    }, 60);

    return () => {
      cancelled = true;
      if (initTimer != null) {
        clearTimeout(initTimer);
        initTimer = null;
      }
      stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const setMutedSafe = (v: boolean) => {
    setMuted(v);
    micRef.current?.setMuted(v);
  };

  if (!open) return null;

  // Pick whichever analyser drives the orb at the moment (assistant if
  // audio recently arrived, mic otherwise). Falls back to a static state.
  const activeAnalyser =
    orbState === "assistant"
      ? playerRef.current?.analyser ?? null
      : micRef.current?.analyser ?? null;

  return (
    <div className="fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-dashed border-outline/20">
        <div className="flex items-center gap-2">
          <span
            className={`w-2 h-2 rounded-full ${
              phase === "ready"
                ? "bg-solar-gold animate-pulse"
                : phase === "connecting"
                ? "bg-amber-400 animate-pulse"
                : "bg-on-surface-variant"
            }`}
          />
          <span className="font-nav-label text-[11px] uppercase tracking-widest text-on-surface-variant">
            {phase === "connecting"
              ? "Connecting…"
              : phase === "ready"
              ? "Voice mode · live"
              : phase === "ended"
              ? "Ended"
              : "Idle"}
          </span>
        </div>
        <button
          onClick={handleClose}
          className="btn-ghost wobbly-border-sm px-3 py-1.5 text-[11px] font-nav-label uppercase tracking-widest flex items-center gap-2 hover:text-rose-400 hover:border-rose-400/60"
        >
          <PhoneOff size={14} />
          End
        </button>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* ── Fixed top: orb + transcript + tool badges ── */}
        <div className="shrink-0 flex flex-col items-center px-6 pt-6 pb-4 gap-4">
          <VoiceOrb analyser={activeAnalyser} state={orbState} size={260} />

          <div className="text-center max-w-md min-h-12">
            {error ? (
              <p className="font-body-md text-sm text-rose-400">{error}</p>
            ) : phase === "connecting" ? (
              <p className="font-body-md text-sm text-on-surface-variant">
                Aligning the cosmic channel…
              </p>
            ) : (
              <>
                {partialUserText && (
                  <p className="font-body-md text-sm text-on-surface-variant mb-1">
                    <span className="text-emerald-500/80">You · </span>
                    {partialUserText}
                  </p>
                )}
                {partialAssistantText && (
                  <p className="font-body-md text-sm text-solar-gold">
                    {partialAssistantText}
                  </p>
                )}
                {!partialUserText && !partialAssistantText && (
                  <p className="font-annotation-sm text-base text-on-surface-variant italic">
                    Speak when you&apos;re ready. The cosmos is listening.
                  </p>
                )}
              </>
            )}
          </div>

          {tools.length > 0 && (
            <div className="flex flex-wrap items-center justify-center gap-1.5 max-w-3xl">
              <span className="flex items-center gap-1 font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant pr-1">
                <Wrench size={10} className="text-solar-gold/70" />
                Activity
              </span>
              {tools.map((t) => (
                <span
                  key={t.id}
                  className="inline-flex items-center gap-1 px-2 py-0.5 wobbly-border-sm bg-surface-container-low/70 border border-outline/30 text-[10px] font-body-md text-on-surface-variant"
                >
                  {t.status === "running" ? (
                    <Loader2 size={10} className="animate-spin text-solar-gold" />
                  ) : t.status === "error" ? (
                    <AlertTriangle size={10} className="text-rose-400" />
                  ) : (
                    <Check size={10} className="text-emerald-400" />
                  )}
                  <span className="font-headline-md">{labelFor(t.tool)}</span>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* ── Scrollable card stack ── */}
        {stack.length > 0 && (
          <div className="flex-1 overflow-y-auto border-t border-dashed border-outline/20 px-6 py-4">
            <div className="w-full max-w-3xl mx-auto flex flex-col gap-6">
              {stack.map((entry) =>
                entry.kind === "chart_svg" ? (
                  <VoiceCardEntry key={entry.id} cardType="birth_chart">
                    <div className="flex justify-center">
                      <ChartSvgCard svg={entry.svg} />
                    </div>
                  </VoiceCardEntry>
                ) : (
                  <VoiceCardEntry key={entry.id} cardType={entry.card_type}>
                    <div className="flex justify-center">
                      <StructuredCard
                        cardType={entry.card_type}
                        data={entry.data}
                      />
                    </div>
                  </VoiceCardEntry>
                )
              )}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-dashed border-outline/20 px-6 py-4 flex items-center justify-center gap-3">
        <button
          onClick={() => setMutedSafe(!muted)}
          disabled={phase !== "ready"}
          className={`btn-ghost wobbly-border-sm px-4 py-2 font-nav-label text-[11px] uppercase tracking-widest flex items-center gap-2 disabled:opacity-50 ${
            muted ? "border-rose-400/60 text-rose-400" : ""
          }`}
        >
          {muted ? <MicOff size={14} /> : <Mic size={14} />}
          {muted ? "Muted" : "Live mic"}
        </button>
        <button
          onClick={handleClose}
          className="btn-primary wobbly-border-sm px-5 py-2 font-nav-label text-[11px] uppercase tracking-widest flex items-center gap-2"
        >
          <PhoneOff size={14} />
          End session
        </button>
      </div>
    </div>
  );
}
