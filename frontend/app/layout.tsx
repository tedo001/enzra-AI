import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RailVision AI — Railway Safety Platform",
  description:
    "Real-time railway hazard detection & collision-risk prediction powered by YOLO26.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen">{children}</body>
    </html>
  );
}
