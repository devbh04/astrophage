import { ReactNode } from "react";

interface CardShellProps {
  title: string;
  badge?: string;
  icon?: ReactNode;
  accent?: "gold" | "violet" | "rose" | "teal";
  children: ReactNode;
}

const ACCENT_BAR: Record<NonNullable<CardShellProps["accent"]>, string> = {
  gold: "bg-solar-gold",
  violet: "bg-[#8b5cf6]",
  rose: "bg-[#f43f5e]",
  teal: "bg-[#14b8a6]",
};

/**
 * Common envelope for every structured chat card.
 * Provides a wobbly border, a tape strip, an accent stripe on the left,
 * and a title row with optional badge.
 */
export default function CardShell({
  title,
  badge,
  icon,
  accent = "gold",
  children,
}: CardShellProps) {
  return (
    <div className="relative max-w-[85%] md:max-w-[75%] glass-panel wobbly-border-sm overflow-hidden">
      <div className="tape-strip" />
      <div className={`absolute left-0 top-0 bottom-0 w-1 ${ACCENT_BAR[accent]}`} />
      <div className="pl-5 pr-5 py-5">
        <div className="flex items-center gap-2 mb-4">
          {icon && <span className="text-solar-gold">{icon}</span>}
          <h3 className="font-headline-md text-base text-primary tracking-tight">
            {title}
          </h3>
          {badge && (
            <span className="ml-auto px-2 py-1 text-[9px] font-nav-label uppercase tracking-widest bg-surface-container text-solar-gold wobbly-border-sm">
              {badge}
            </span>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}
