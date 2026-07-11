import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TradeKnox — Institutional-Grade Forex Trading Bot",
  description: "12-layer signal pipeline. SMC 8-Gate strategy. 20+ years backtested across 8 forex pairs. TradeKnox delivers institutional-quality signals with surgical precision.",
  keywords: ["forex", "trading bot", "SMC", "smart money concepts", "forex signals", "algorithmic trading", "order blocks", "BOS", "CHoCH"],
  icons: {
    icon: "/logo.svg",
  },
  openGraph: {
    title: "TradeKnox — Institutional-Grade Forex Trading Bot",
    description: "12-layer signal pipeline. SMC 8-Gate strategy. 20+ years backtested across 8 forex pairs.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}