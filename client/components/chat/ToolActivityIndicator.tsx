interface ToolActivityIndicatorProps {
  toolName: string;
  display: string;
}

const TOOL_MESSAGES: Record<string, string> = {
  reasoning: "Consulting the stars...",
  compute_birth_chart: "Mapping your celestial blueprint...",
  geocode_place: "Locating the coordinates of destiny...",
  compute_dasha_periods: "Calculating your Dasha timeline...",
  compute_nakshatra_details: "Reading your birth star...",
  check_sade_sati: "Examining Saturn's influence...",
  get_panchang: "Checking today's Panchang...",
  kundali_milan: "Comparing cosmic signatures...",
  compute_muhurta: "Finding auspicious windows...",
  get_daily_transits: "Tracking planetary movements...",
  knowledge_lookup: "Searching ancient wisdom...",
  render_chart_svg: "Drawing your chart...",
  get_current_sky: "Observing the current sky...",
};

export default function ToolActivityIndicator({
  toolName,
  display,
}: ToolActivityIndicatorProps) {
  const message = TOOL_MESSAGES[toolName] || display || "Processing...";

  return (
    <div className="flex justify-start animate-in fade-in slide-in-from-bottom-2 duration-300">
      <div className="flex items-center gap-3 px-5 py-3 glass-panel wobbly-border-sm">
        {/* Pulsing dots */}
        <div className="flex gap-1">
          <span
            className="w-2 h-2 rounded-full bg-solar-gold animate-pulse"
            style={{ animationDelay: "0ms" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-solar-gold animate-pulse"
            style={{ animationDelay: "150ms" }}
          />
          <span
            className="w-2 h-2 rounded-full bg-solar-gold animate-pulse"
            style={{ animationDelay: "300ms" }}
          />
        </div>
        <span className="font-annotation-sm text-sm text-solar-gold">
          {message}
        </span>
      </div>
    </div>
  );
}
