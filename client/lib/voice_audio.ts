/**
 * Browser audio plumbing for voice mode.
 *
 * - ``startMicCapture`` opens the mic and pumps 16 kHz PCM16 chunks into
 *   the supplied callback. Uses an AudioWorklet at /voice/mic-worklet.js.
 * - ``createPlayer`` returns a 24 kHz PCM16 sink: feed it raw bytes and
 *   it queues them into AudioBufferSourceNodes back-to-back with no gaps.
 * - Each side exposes an AnalyserNode so the orb visualizer can read
 *   frequency data without owning the audio graph itself.
 */

const INPUT_SAMPLE_RATE = 16000;
const OUTPUT_SAMPLE_RATE = 24000;

export interface MicCapture {
  context: AudioContext;
  analyser: AnalyserNode;
  stop: () => void;
  setMuted: (muted: boolean) => void;
}

export async function startMicCapture(
  onChunk: (pcm16: ArrayBuffer) => void
): Promise<MicCapture> {
  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
      channelCount: 1,
    },
    video: false,
  });

  // Use the device's native rate for the mic; we resample inside the worklet.
  const context = new AudioContext();
  await context.audioWorklet.addModule("/voice/mic-worklet.js");

  const source = context.createMediaStreamSource(stream);
  const worklet = new AudioWorkletNode(context, "mic-worklet");
  const analyser = context.createAnalyser();
  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.55;

  // mic -> [analyser, worklet]; never touch destination so we don't echo.
  source.connect(analyser);
  source.connect(worklet);

  let muted = false;
  worklet.port.onmessage = (e) => {
    if (muted) return;
    onChunk(e.data as ArrayBuffer);
  };

  return {
    context,
    analyser,
    stop: () => {
      try {
        worklet.disconnect();
      } catch {
        /* noop */
      }
      try {
        source.disconnect();
      } catch {
        /* noop */
      }
      try {
        analyser.disconnect();
      } catch {
        /* noop */
      }
      stream.getTracks().forEach((t) => t.stop());
      context.close().catch(() => {});
    },
    setMuted: (v: boolean) => {
      muted = v;
    },
  };
}

export interface AudioPlayer {
  context: AudioContext;
  analyser: AnalyserNode;
  push: (pcm16: ArrayBuffer) => void;
  reset: () => void;
  close: () => void;
}

/**
 * 24 kHz PCM16 player. Schedules each chunk back-to-back so output is
 * gapless. ``reset`` cancels everything currently queued (used when the
 * model interrupts itself or a new turn starts).
 */
export function createPlayer(): AudioPlayer {
  const context = new AudioContext({ sampleRate: OUTPUT_SAMPLE_RATE });
  const gain = context.createGain();
  gain.gain.value = 1.0;
  const analyser = context.createAnalyser();
  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.6;

  gain.connect(analyser);
  analyser.connect(context.destination);

  let cursor = context.currentTime;
  let activeSources: AudioBufferSourceNode[] = [];

  function push(buf: ArrayBuffer) {
    if (buf.byteLength === 0) return;
    // Int16 → Float32
    const view = new DataView(buf);
    const samples = view.byteLength / 2;
    const audioBuffer = context.createBuffer(1, samples, OUTPUT_SAMPLE_RATE);
    const ch0 = audioBuffer.getChannelData(0);
    for (let i = 0; i < samples; i++) {
      const s = view.getInt16(i * 2, true);
      ch0[i] = s < 0 ? s / 0x8000 : s / 0x7fff;
    }
    const src = context.createBufferSource();
    src.buffer = audioBuffer;
    src.connect(gain);
    const start = Math.max(cursor, context.currentTime);
    src.start(start);
    cursor = start + audioBuffer.duration;
    activeSources.push(src);
    src.onended = () => {
      activeSources = activeSources.filter((s) => s !== src);
    };
  }

  function reset() {
    for (const s of activeSources) {
      try {
        s.stop();
      } catch {
        /* noop */
      }
      try {
        s.disconnect();
      } catch {
        /* noop */
      }
    }
    activeSources = [];
    cursor = context.currentTime;
  }

  function close() {
    reset();
    try {
      gain.disconnect();
    } catch {
      /* noop */
    }
    try {
      analyser.disconnect();
    } catch {
      /* noop */
    }
    context.close().catch(() => {});
  }

  return { context, analyser, push, reset, close };
}

export const VOICE_RATES = { input: INPUT_SAMPLE_RATE, output: OUTPUT_SAMPLE_RATE };
