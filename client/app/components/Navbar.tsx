import Link from 'next/link';

export default function Navbar() {
  return (
    <nav className="fixed top-0 w-full z-50 flex justify-between items-center px-margin-mobile md:px-margin-desktop py-6 max-w-full border-b border-dashed border-outline/20 bg-background/80 backdrop-blur-md">
      <div className="font-annotation-sm text-display-lg-mobile md:text-headline-md tracking-tighter text-primary">
        ASTROPHAGE
      </div>
      <div className="hidden md:flex space-x-8">
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="#"
        >
          Ephemeral
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="#"
        >
          Transits
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="#"
        >
          Synastry
        </Link>
        <Link
          className="font-nav-label text-nav-label uppercase tracking-[0.15em] text-on-surface-variant hover:text-primary transition-colors hover:bg-secondary-container/10 transition-all duration-300 py-2 px-3 rounded"
          href="#"
        >
          Log
        </Link>
      </div>
      <button className="hidden md:flex font-nav-label text-nav-label uppercase tracking-[0.15em] px-6 py-2 border border-primary wobbly-border-sm items-center gap-2 hover:bg-secondary-container/10 hover:text-primary transition-all duration-300 hover:translate-x-1 hover:translate-y-1">
        <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>
          explore
        </span>
        Decode Destiny
      </button>
      <button className="md:hidden text-primary">
        <span className="material-symbols-outlined">menu</span>
      </button>
    </nav>
  );
}
