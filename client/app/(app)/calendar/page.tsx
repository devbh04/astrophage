"use client";

export default function CalendarPage() {
  const today = new Date();
  const year = today.getFullYear();
  const month = today.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayOfWeek = new Date(year, month, 1).getDay();

  const monthName = today.toLocaleString("default", { month: "long" });
  const days = Array.from({ length: daysInMonth }, (_, i) => i + 1);
  const emptySlots = Array.from({ length: firstDayOfWeek }, (_, i) => i);

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
            {monthName.toUpperCase()} {year}
          </p>
        </div>
        <button className="btn-primary wobbly-border-sm px-6 py-3 font-nav-label text-xs uppercase tracking-widest">
          FIND MUHURTA
        </button>
      </div>

      {/* Day headers */}
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

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-2">
        {emptySlots.map((i) => (
          <div key={`empty-${i}`} />
        ))}
        {days.map((day) => {
          const isToday = day === today.getDate();
          return (
            <button
              key={day}
              className={`aspect-square flex flex-col items-center justify-center p-2 wobbly-border-sm transition-all hover:bg-surface-container group
                ${
                  isToday
                    ? "bg-surface-container border-solar-gold"
                    : "bg-surface-container-lowest border-outline/20"
                }`}
            >
              <span
                className={`font-headline-md text-sm ${
                  isToday ? "text-solar-gold" : "text-primary"
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

      {/* Panchang placeholder */}
      <div className="mt-8 glass-panel wobbly-border p-6">
        <h3 className="font-headline-md text-lg text-primary mb-4 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-solar-gold" />
          Today&apos;s Panchang
        </h3>
        <p className="font-body-md text-sm text-on-surface-variant">
          Click any day to see its full Panchang details. The Panchang tool
          will be connected in Phase 2 to show Tithi, Nakshatra, Rahu Kaal,
          and auspiciousness ratings.
        </p>
      </div>
    </div>
  );
}
