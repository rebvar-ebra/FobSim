"use client";

import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import Sidebar from "./Sidebar";
import { Menu } from "lucide-react";

export default function ClientWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname?.startsWith("/auth");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  // Close sidebar on navigation (mobile)
  useEffect(() => {
    setIsSidebarOpen(false);
  }, [pathname]);

  return (
    <>
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />
      
      {!isAuthPage && (
        <button 
          onClick={() => setIsSidebarOpen(true)}
          className="lg:hidden fixed top-4 left-4 z-40 p-2 bg-slate-800 rounded-lg text-white shadow-lg border border-slate-700"
        >
          <Menu size={20} />
        </button>
      )}

      <main className={`${isAuthPage ? "" : "lg:pl-64"} min-h-screen transition-all duration-300`}>
        <div className={`${isAuthPage ? "p-0" : "p-4 md:p-8"} w-full`}>
          {children}
        </div>
      </main>
      
      {/* Overlay for mobile */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
    </>
  );
}
