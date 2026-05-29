"use client";

import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { panchangApi, profilesApi, type PanchangData } from "@/lib/api";
import PanchangCard from "@/components/cards/PanchangCard";
import MuhurtaDialog from "@/components/calendar/MuhurtaDialog";

const fmtDate = (d: Date) => {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
};

export default function CalendarPage() {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth());
  const [selectedDate, setSelectedDate] = useState<string>(fmtDate(today));
  const [panchang, setPanchang] = useState<PanchangData | null>(null);
  const [loading, setLoading] = useState(false);
  const [muhurtaOpen, setMuhurtaOpen] = useState(false);
  const [coords, setCoords] = useState<{
    lat: number;
    lng: number;
    timezone: string;
    place: string;
  }>({ lat: 19.076, lng: 72.8777, timezone: "Asia/Kolkata", place: "Mumbai" });

  // Default coords come from the user's self profile if available
  useEffect(() => {
    profilesApi
      .list()
      .then((profiles) => {
        const self = profiles.find((p) => p.relationship === "self");
        if (self) {
          setCoords({
            lat: self.lat,
            lng: self.lng,
            timezone: self.timezone,
            place: self.place_name || "—",
          });
        }
      })
      .catch(() => { });
  }, []);

  const fetchPanchang = async (date: string) => {
    setLoading(true);
    try {
      const data = await panchangApi.forDate(
        date,
        coords.lat,
        coords.lng,
        coords.timezone
      );
      setPanchang(data);
    } catch (err) {
      console.error(err);
      setPanchang(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPanchang(selectedDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, coords.lat, coords.lng, coords.timezone]);

  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();
  const monthName = new Date(year, month, 1).toLocaleString("default", {
    month: "long",
  });
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const emptySlots = Array.from({ length: firstDayOfWeek }, (_, i) => i);

  const goPrev = () => {
    if (month === 0) {
      setMonth(11);
      setYear((y) => y - 1);
    } else {
      setMonth((m) => m - 1);
    }
  };
  const goNext = () => {
    if (month === 11) {
      setMonth(0);
      setYear((y) => y + 1);
    } else {
      setMonth((m) => m + 1);
    }
  };

  const [sy, sm, sd] = selectedDate.split("-").map(Number);
  const fmtSelected = new Date(sy, sm - 1, sd).toLocaleDateString(undefined, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });

  return (
    <div className="p-6 md:p-8 max-w-7xl mx-auto">
      <div className="flex flex-col mb-6 gap-4 sm:gap-8">
        <div className="flex-1">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-4">
            <h2 className="font-headline-md text-2xl text-primary mb-1">
              Auspicious{" "}
              <span className="font-annotation-sm text-3xl text-solar-gold">
                Calendar
              </span>
              <p className="font-nav-label text-[10px] text-on-surface-variant uppercase tracking-[0.2em] mt-2 mb-4">
                {fmtSelected.toUpperCase()} · {coords.place}
              </p>
            </h2>
            <button
              onClick={() => setMuhurtaOpen(true)}
              className="btn-primary wobbly-border-sm px-5 py-3 sm:py-2.5 h-min font-nav-label text-xs uppercase tracking-widest sm:mt-2 whitespace-nowrap w-full sm:w-auto"
            >
              Find Muhurta
            </button>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between w-full mt-2 gap-4 sm:gap-0">
            <div className="border-l-2 border-solar-gold pl-4 py-1">
              <p className="font-body-md text-sm text-on-surface-variant leading-relaxed">
                Select any day to view its complete <b>Panchang</b>
              </p>
            </div>
            <div className="border-l-2 sm:border-l-0 sm:border-r-2 border-solar-gold pl-4 sm:pl-0 sm:pr-4 py-1 text-left sm:text-right">
              <p className="font-body-md text-sm text-on-surface-variant leading-relaxed">
                Select your activity and date to find the most auspicious <b>Muhurta</b> (timings).
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[2fr_3fr] items-start">
        {/* LEFT — Panchang card */}
        <div className="flex">
          {loading ? (
            <div className="glass-panel wobbly-border p-6 w-full text-center font-body-md text-sm text-on-surface-variant">
              Loading panchang…
            </div>
          ) : panchang ? (
            <div className="w-full">
              <PanchangCard data={panchang} fullWidth />
            </div>
          ) : (
            <div className="glass-panel wobbly-border p-6 w-full text-center font-body-md text-sm text-on-surface-variant">
              No panchang available for this date.
            </div>
          )}
        </div>

        {/* RIGHT — compact calendar */}
        <div className="glass-panel wobbly-border p-4">
          <div className="flex items-center justify-between mb-3">
            <button
              onClick={goPrev}
              className="p-1.5 rounded-md hover:bg-surface-container text-on-surface-variant hover:text-solar-gold"
              aria-label="Previous month"
            >
              <ChevronLeft size={16} />
            </button>
            <div className="text-center">
              <div className="font-headline-md text-base text-primary leading-tight">
                {monthName}
              </div>
              <div className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant">
                {year}
              </div>
            </div>
            <button
              onClick={goNext}
              className="p-1.5 rounded-md hover:bg-surface-container text-on-surface-variant hover:text-solar-gold"
              aria-label="Next month"
            >
              <ChevronRight size={16} />
            </button>
          </div>

          <button
            onClick={() => {
              const t = new Date();
              setYear(t.getFullYear());
              setMonth(t.getMonth());
              setSelectedDate(fmtDate(t));
            }}
            className="w-full text-center font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-solar-gold py-1 mb-2 border-b border-dashed border-outline/20"
          >
            Today
          </button>

          <div className="grid grid-cols-7 gap-1 mb-1">
            {["S", "M", "T", "W", "T", "F", "S"].map((d, i) => (
              <div
                key={i}
                className="text-center font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant py-1"
              >
                {d}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7 gap-1">
            {emptySlots.map((i) => (
              <div key={`empty-${i}`} />
            ))}
            {days.map((day) => {
              const dateStr = fmtDate(new Date(year, month, day));
              const isToday =
                day === today.getDate() &&
                month === today.getMonth() &&
                year === today.getFullYear();
              const isSelected = dateStr === selectedDate;
              return (
                <button
                  key={day}
                  onClick={() => setSelectedDate(dateStr)}
                  className={`aspect-square flex items-center justify-center wobbly-border-sm transition-all text-sm
                    ${isSelected
                      ? "bg-solar-gold/25 border-solar-gold/70 text-solar-gold ring-1 ring-solar-gold/40"
                      : isToday
                        ? "bg-surface-container border-solar-gold/60 text-solar-gold"
                        : "bg-surface-container-lowest border-outline/20 text-primary hover:bg-surface-container/60"
                    }`}
                >
                  <span className="font-headline-md leading-none">{day}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-4 pt-3 border-t border-dashed border-outline/20 space-y-1.5">
            <div className="flex items-center justify-between text-[11px]">
              <span className="font-nav-label text-[9px] uppercase tracking-widest text-on-surface-variant">
                Selected
              </span>
              <span className="font-headline-md text-primary">{fmtSelected}</span>
            </div>
            <div className="flex items-center gap-3 text-[10px] font-body-md text-on-surface-variant">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 wobbly-border-sm bg-solar-gold/30 border border-solar-gold/60" />
                Today
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 wobbly-border-sm bg-solar-gold/25 border border-solar-gold/70" />
                Selected
              </span>
            </div>
          </div>
        </div>
      </div>

      <MuhurtaDialog
        open={muhurtaOpen}
        onOpenChange={setMuhurtaOpen}
        defaultLat={coords.lat}
        defaultLng={coords.lng}
        defaultTimezone={coords.timezone}
      />
    </div>
  );
}
