import Link from 'next/link';

export default function Footer() {
  return (
    <footer className="w-full grid grid-cols-4 md:grid-cols-12 gap-gutter px-margin-mobile md:px-margin-desktop py-12 relative overflow-hidden border-t-2 border-primary bg-surface-container z-20 mt-20">
      <div className="col-span-4 md:col-span-3">
        <div className="font-headline-md text-headline-md text-primary mb-4">ASTROPHAGE</div>
        <p className="font-annotation-sm text-annotation-sm text-on-surface-variant max-w-xs">
          Decoding the cosmic radiance through an editorial lens.
        </p>
      </div>
      <div className="col-span-4 md:col-start-5 md:col-span-4 flex flex-col gap-4 mt-8 md:mt-0">
        <Link
          className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant hover:text-primary hover:underline decoration-dashed decoration-1 transition-all duration-500 ease-in-out"
          href="#"
        >
          Archives
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant hover:text-primary hover:underline decoration-dashed decoration-1 transition-all duration-500 ease-in-out"
          href="#"
        >
          Ethics
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant hover:text-primary hover:underline decoration-dashed decoration-1 transition-all duration-500 ease-in-out"
          href="#"
        >
          Privacy
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-widest text-on-surface-variant hover:text-primary hover:underline decoration-dashed decoration-1 transition-all duration-500 ease-in-out"
          href="#"
        >
          Terms
        </Link>
      </div>
      <div className="col-span-4 md:col-start-9 md:col-span-4 text-left md:text-right flex flex-col justify-end mt-8 md:mt-0">
        <div className="font-nav-label text-nav-label text-on-surface uppercase tracking-widest">
          ©2024 ASTROPHAGE EDITORIAL. ALL RIGHTS RESERVED.
        </div>
      </div>
    </footer>
  );
}
