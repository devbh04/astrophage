export default function EditorialSection() {
  return (
    <section className="py-32 px-margin-mobile md:px-margin-desktop relative z-10 border-t border-dashed border-outline/20">
      <div className="max-w-[1440px] mx-auto">
        <div className="grid grid-cols-4 md:grid-cols-12 gap-gutter items-center">
          <div className="col-span-4 md:col-start-3 md:col-span-8 relative fade-in-up text-center">
            <div className="tape-strip"></div>
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              alt="Planetary Alignment Gems"
              className="w-full h-auto object-cover grayscale-transition wobbly-border shadow-[8px_8px_0px_0px_rgba(26,28,27,0.1)] mx-auto"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuB8y5Nr4-UJTtRfZa3qXrz_FEsUOQbw3p1UXxktXu9x7jCXn20AprVpnywt045oHOmvH4DLMccwMBIAxgX8SFVbcm228JxIwYCYsyl6ojE8oi59MnhF71Zp1KmSp-TYj_ttr_PWlA8qXN0mUbegOoLRUgm99KtPiZ0XLmSBRfFEDjZY7UJTtgibTaD5rmvqB97VWZrvH4Ctf1CAxRr4qFpvgoCSqRdkN1mm_2lPQTEplsAQFhjTwa1zBXy-XGrZhrmytL2A4_66JUo"
            />
            <div className="absolute -right-10 top-1/2 -translate-y-1/2 vertical-text font-nav-label text-xs tracking-[0.2em] text-outline opacity-60 hidden md:block">
              EDITORIAL // 06 — CELESTIAL MECHANICS
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
