import React from "react";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import ClientWrapper from "@/app/components/ClientWrapper";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FobSim Platform",
  description: "Advanced Blockchain Simulation & Analytics Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} text-white bg-[#0f1021]`}>
        <ClientWrapper>{children}</ClientWrapper>
      </body>
    </html>
  );
}
