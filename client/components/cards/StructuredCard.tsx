import BirthChartCard from "./BirthChartCard";
import DashaTimelineCard from "./DashaTimelineCard";
import NakshatraCard from "./NakshatraCard";
import SadeSatiCard from "./SadeSatiCard";
import PanchangCard from "./PanchangCard";
import MuhurtaCard from "./MuhurtaCard";
import DailyTransitsCard from "./DailyTransitsCard";
import CurrentSkyCard from "./CurrentSkyCard";
import KundaliMilanCard from "./KundaliMilanCard";
import KnowledgeCard from "./KnowledgeCard";
import CardShell from "./CardShell";

interface Props {
  cardType: string;
  data: unknown;
}

/**
 * Routes a structured_card frame to the right visual renderer based on
 * card_type. Falls back to a JSON dump for unknown types.
 */
export default function StructuredCard({ cardType, data }: Props) {
  switch (cardType) {
    case "birth_chart":
      return <BirthChartCard data={data as never} />;
    case "dasha_timeline":
      return <DashaTimelineCard data={data as never} />;
    case "nakshatra":
      return <NakshatraCard data={data as never} />;
    case "sade_sati":
      return <SadeSatiCard data={data as never} />;
    case "panchang":
      return <PanchangCard data={data as never} />;
    case "muhurta":
      return <MuhurtaCard data={data as never} />;
    case "daily_transits":
      return <DailyTransitsCard data={data as never} />;
    case "current_sky":
      return <CurrentSkyCard data={data as never} />;
    case "kundali_milan":
      return <KundaliMilanCard data={data as never} />;
    case "knowledge":
      return <KnowledgeCard data={data as never} />;
    default:
      return (
        <CardShell title={cardType.replace(/_/g, " ")} accent="violet">
          <pre className="font-mono text-[10px] text-on-surface-variant whitespace-pre-wrap break-all">
            {JSON.stringify(data, null, 2)}
          </pre>
        </CardShell>
      );
  }
}
