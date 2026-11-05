"use client";

import { ReactNode, useEffect, useSyncExternalStore } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";

const subscribeToSession = () => () => {};
const getSessionSnapshot = () => Boolean(localStorage.getItem("token"));
const getServerSessionSnapshot = () => false;

export default function RequireAuth({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const authorized = useSyncExternalStore(
    subscribeToSession,
    getSessionSnapshot,
    getServerSessionSnapshot,
  );

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      const nextPath = pathname || "/";
      router.replace(`/auth/login?next=${encodeURIComponent(nextPath)}`);
      return;
    }

  }, [authorized, pathname, router]);

  if (!authorized) {
    return (
      <div className="min-h-screen bg-[#0f1021] flex items-center justify-center text-slate-400">
        <div className="flex items-center gap-3 text-sm font-bold">
          <Loader2 className="animate-spin text-cyan-400" size={20} />
          Checking your session…
        </div>
      </div>
    );
  }

  return children;
}
