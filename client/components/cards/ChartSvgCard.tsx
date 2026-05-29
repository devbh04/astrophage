import { Sparkles } from "lucide-react";
import CardShell from "./CardShell";

interface Props {
  svg: string;
}

export default function ChartSvgCard({ svg }: Props) {
  return (
    <CardShell title="Chart Visualization" icon={<Sparkles size={16} />} accent="gold">
      <div
        className="w-full flex justify-center bg-surface-container-lowest/40 wobbly-border-sm p-3"
        // SVG is generated server-side by render_chart_svg — pure markup, no script tags.
        dangerouslySetInnerHTML={{ __html: svg }}
      />
    </CardShell>
  );
}
