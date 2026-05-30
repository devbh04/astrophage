"use client";

import { useEffect, useRef } from "react";

interface Props {
  /** AnalyserNode whose frequency data drives the orb's pulse. */
  analyser: AnalyserNode | null;
  /** "user" tints cool, "assistant" tints gold, "idle" stays still. */
  state: "user" | "assistant" | "idle";
  size?: number;
}

const RING_COUNT = 64;

/**
 * Circular waveform orb.
 *
 * Draws ``RING_COUNT`` short radial bars around a circle. Their length is
 * driven by the live frequency-bin amplitudes of the supplied analyser.
 * When idle (no analyser, or all-zero amplitudes) the bars settle into a
 * gentle breathing animation so the orb never goes flat.
 */
export default function VoiceOrb({ analyser, state, size = 280 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number | null>(null);
  const phaseRef = useRef(0);
  const targetsRef = useRef<Float32Array>(new Float32Array(RING_COUNT));
  const valuesRef = useRef<Float32Array>(new Float32Array(RING_COUNT));

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = typeof window !== "undefined" ? window.devicePixelRatio || 1 : 1;
    canvas.width = size * dpr;
    canvas.height = size * dpr;
    canvas.style.width = `${size}px`;
    canvas.style.height = `${size}px`;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    const colours = {
      assistant: { ring: "#c89b3c", glow: "#f5e7c3", core: "rgba(200,155,60,0.18)" },
      user: { ring: "#5b8a72", glow: "#cfe3d3", core: "rgba(91,138,114,0.18)" },
      idle: { ring: "#8a8270", glow: "#e8dcb6", core: "rgba(138,130,112,0.10)" },
    };

    const freq = analyser ? new Uint8Array(analyser.frequencyBinCount) : null;

    const render = () => {
      const now = performance.now() / 1000;
      phaseRef.current += 0.012;

      // Build target amplitudes per ring bar.
      const targets = targetsRef.current;
      if (analyser && freq) {
        analyser.getByteFrequencyData(freq);
        const step = Math.max(1, Math.floor(freq.length / RING_COUNT));
        for (let i = 0; i < RING_COUNT; i++) {
          let s = 0;
          let n = 0;
          for (let j = 0; j < step; j++) {
            const idx = i * step + j;
            if (idx < freq.length) {
              s += freq[idx];
              n++;
            }
          }
          const v = n > 0 ? s / n / 255 : 0;
          targets[i] = v;
        }
      } else {
        for (let i = 0; i < RING_COUNT; i++) targets[i] = 0;
      }

      // Idle breathing — modulate by a slow sine so the orb never freezes.
      const breath = 0.18 + 0.07 * Math.sin(now * 1.3);

      // Smooth values toward targets.
      const values = valuesRef.current;
      for (let i = 0; i < RING_COUNT; i++) {
        const target = Math.max(targets[i], breath);
        values[i] += (target - values[i]) * 0.18;
      }

      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      const cx = w / 2;
      const cy = h / 2;
      const baseRadius = Math.min(w, h) * 0.30;
      const palette = colours[state];

      ctx.clearRect(0, 0, w, h);

      // Soft glow disc behind everything.
      const grad = ctx.createRadialGradient(cx, cy, baseRadius * 0.4, cx, cy, baseRadius * 1.6);
      grad.addColorStop(0, palette.glow + "");
      grad.addColorStop(0.5, palette.core);
      grad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      // Inner solid circle (core).
      ctx.beginPath();
      ctx.arc(cx, cy, baseRadius * 0.55, 0, Math.PI * 2);
      ctx.fillStyle = palette.core;
      ctx.fill();

      // Faint outer ring.
      ctx.beginPath();
      ctx.arc(cx, cy, baseRadius * 1.05, 0, Math.PI * 2);
      ctx.strokeStyle = palette.ring + "55";
      ctx.lineWidth = 1;
      ctx.stroke();

      // Radial bars.
      ctx.strokeStyle = palette.ring;
      ctx.lineCap = "round";
      const maxLen = baseRadius * 0.7;
      for (let i = 0; i < RING_COUNT; i++) {
        const angle = (i / RING_COUNT) * Math.PI * 2 + phaseRef.current;
        const v = values[i];
        const inner = baseRadius * 0.78;
        const outer = inner + maxLen * v;
        ctx.lineWidth = 2 + v * 2.5;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * inner, cy + Math.sin(angle) * inner);
        ctx.lineTo(cx + Math.cos(angle) * outer, cy + Math.sin(angle) * outer);
        ctx.globalAlpha = 0.35 + v * 0.65;
        ctx.stroke();
      }
      ctx.globalAlpha = 1;

      rafRef.current = requestAnimationFrame(render);
    };

    rafRef.current = requestAnimationFrame(render);
    return () => {
      if (rafRef.current != null) cancelAnimationFrame(rafRef.current);
    };
  }, [analyser, state, size]);

  return (
    <canvas
      ref={canvasRef}
      className="block"
      style={{ width: size, height: size }}
      aria-hidden
    />
  );
}
