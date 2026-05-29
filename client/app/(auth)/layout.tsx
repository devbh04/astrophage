import GridLines from "@/app/components/GridLines";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative min-h-screen flex items-center justify-center px-margin-mobile md:px-margin-desktop">
      <GridLines />
      <div className="relative z-10 w-full max-w-md">{children}</div>
    </div>
  );
}
