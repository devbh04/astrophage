"use client";

import { useEffect, useState } from "react";
import { panchangApi, profilesApi, type PanchangData } from "@/lib/api";
import PanchangCard from "@/components/cards/PanchangCard";
import MuhurtaDialog from "@/components/calendar/MuhurtaDialog";

const fmtDate = (d: Date) => d.toISOString().slice(0, 10);

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
      .catch(() => {});
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

  return (
    <div className="p-6 md:p-8 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="font-headline-md text-2xl text-primary mb-2">
            Auspicious{" "}
            <span className="font-annotation-sm text-3xl text-solar-gold">
              Calendar
            </span>
          </h2>
          <p className="font-nav-label text-nav-label text-on-surface-variant uppercase tracking-[0.2em]">
            {monthName.toUpperCase()} {year} · {coords.place}
          </p>
        </div>
        <button
          onClick={() => setMuhurtaOpen(true)}
          className="btn-primary wobbly-border-sm px-6 py-3 font-nav-label text-xs uppercase tracking-widest"
        >
          FIND MUHURTA
        </button>
      </div>

      <div className="flex items-center justify-between mb-3 px-1">
        <button
          onClick={goPrev}
          className="font-nav-label text-xs uppercase tracking-widest text-on-surface-variant hover:text-solar-gold"
        >
          ← Prev
        </button>
        <button
          onClick={() => {
            const t = new Date();
            setYear(t.getFullYear());
            setMonth(t.getMonth());
            setSelectedDate(fmtDate(t));
          }}
          className="font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant hover:text-solar-gold"
        >
          Today
        </button>
        <button
          onClick={goNext}
          className="font-nav-label text-xs uppercase tracking-widest text-on-surface-variant hover:text-solar-gold"
        >
          Next →
        </button>
      </div>

      <div className="grid grid-cols-7 gap-2 mb-2">
        {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => (
          <div
            key={day}
            className="text-center font-nav-label text-[10px] uppercase tracking-widest text-on-surface-variant py-2"
          >
            {day}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7 gap-2 mb-8">
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
              className={`aspect-square flex flex-col items-center justify-center p-2 wobbly-border-sm transition-all hover:bg-surface-container
                ${
                  isSelected
                    ? "bg-solar-gold/20 border-solar-gold/60 ring-1 ring-solar-gold/40"
                    : isToday
                    ? "bg-surface-container border-solar-gold"
                    : "bg-surface-container-lowest border-outline/20"
                }`}
            >
              <span
                className={`font-headline-md text-sm ${
                  isSelected
                    ? "text-solar-gold"
                    : isToday
                    ? "text-solar-gold"
                    : "text-primary"
                }`}
              >
                {day}
              </span>
              {isToday && (
                <span className="w-1.5 h-1.5 rounded-full bg-solar-gold mt-1" />
              )}
            </button>
          );
        })}
      </div>

      <div>
        {loading ? (
          <div className="glass-panel wobbly-border p-6 text-center font-body-md text-sm text-on-surface-variant">
            Loading panchang…
          </div>
        ) : panchang ? (
          <div className="flex justify-start">
            <PanchangCard data={panchang} />
          </div>
        ) : (
          <div className="glass-panel wobbly-border p-6 text-center font-body-md text-sm text-on-surface-variant">
            No panchang available for this date.
          </div>
        )}
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
