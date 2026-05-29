import GridLines from "./components/GridLines";
import Navbar from "./components/Navbar";
import HeroSection from "./components/HeroSection";
import EditorialSection from "./components/EditorialSection";
import Features from "./components/Features";
import Footer from "./components/Footer";
import ScrollObserver from "./components/ScrollObserver";

export default function Home() {
  return (
    <>
      <ScrollObserver />
      <GridLines />
      <Navbar />
      <main className="pt-24 relative z-10">
        <HeroSection />
        <Features />
        <EditorialSection />
      </main>
      <Footer />
    </>
  );
}
