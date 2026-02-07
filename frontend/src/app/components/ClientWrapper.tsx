"use client";

import { usePathname } from "next/navigation";
import Sidebar from "./Sidebar";

export default function ClientWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith("/auth");

  return (
    <>
      <Sidebar />
      <main className={`${isAuthPage ? "" : "pl-64"} min-h-screen`}>
        <div className={`${isAuthPage ? "p-0" : "p-8"} w-full`}>
          {children}
        </div>
      </main>
    </>
  );
}
