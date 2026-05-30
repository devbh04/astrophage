/**
 * AudioWorklet that downsamples the mic's native sample rate (typically
 * 44.1k or 48k) to 16 kHz mono Int16 PCM and posts ~32 ms chunks back to
 * the main thread.
 *
 * The browser's AudioContext sampleRate is read at creation time; the
 * worklet uses ``sampleRate`` (a global available inside worklets) to
 * compute the resampling step.
 */

class MicWorklet extends AudioWorkletProcessor {
  constructor() {
    super();
    this.targetRate = 16000;
    this.ratio = sampleRate / this.targetRate;
    // Buffer ~512 target samples (~32 ms) before flushing.
    this.flushSize = 512;
    this.buffer = [];
    this.acc = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const ch = input[0];
    if (!ch) return true;

    // Linear-interpolation downsample; cheap but good enough for voice.
    for (let i = 0; i < ch.length; i++) {
      this.acc += 1;
      if (this.acc >= this.ratio) {
        this.acc -= this.ratio;
        // Clamp + convert Float32 [-1,1] → Int16
        const v = Math.max(-1, Math.min(1, ch[i]));
        this.buffer.push(v < 0 ? v * 0x8000 : v * 0x7fff);
        if (this.buffer.length >= this.flushSize) {
          const out = new Int16Array(this.buffer);
          this.buffer = [];
          this.port.postMessage(out.buffer, [out.buffer]);
        }
      }
    }
    return true;
  }
}

registerProcessor("mic-worklet", MicWorklet);
