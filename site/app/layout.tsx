import type { Metadata } from "next";
import { Geist, Geist_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import NavBar from "@/components/NavBar";
import Footer from "@/components/Footer";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"], display: "swap" });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"], display: "swap" });
const spaceGrotesk = Space_Grotesk({ variable: "--font-space-grotesk", subsets: ["latin"], display: "swap" });

export const metadata: Metadata = {
  title: { default: "WC2026 Quiniela — Probabilistic World Cup Predictions", template: "%s · WC2026 Quiniela" },
  description:
    "Open-source probabilistic predictions for the 2026 FIFA World Cup. 104 matches, a four-model ensemble and Monte Carlo bracket simulation, calibrated 1X2 + advancement probabilities for all 48 nations.",
  metadataBase: new URL("https://wc2026-quiniela.vercel.app"),
  openGraph: {
    title: "WC2026 Quiniela",
    description: "Open-source probabilistic predictions for the 2026 FIFA World Cup.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} ${spaceGrotesk.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <NavBar />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
