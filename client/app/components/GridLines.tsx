export default function GridLines() {
  return (
    <>
      <div className="grid-lines hidden md:grid fixed top-0 left-0 right-0 bottom-0 pointer-events-none z-0 grid-cols-12 gap-gutter px-margin-desktop opacity-5">
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-r border-dashed border-primary h-screen" />
      </div>
      <div className="grid-lines grid md:hidden fixed top-0 left-0 right-0 bottom-0 pointer-events-none z-0 grid-cols-4 gap-5 px-margin-mobile opacity-5">
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-dashed border-primary h-screen" />
        <div className="border-l border-r border-dashed border-primary h-screen" />
      </div>
    </>
  );
}
