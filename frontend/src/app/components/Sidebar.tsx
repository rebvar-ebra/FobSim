"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  History,
  Settings,
  PlayCircle,
  LogOut,
  User,
  Box,
  LayoutDashboard
} from "lucide-react";

import { useState, useEffect } from "react";

import { API_URL } from "../api";

export default function Sidebar() {
  const pathname = usePathname();
  const [user, setUser] = useState<{ email: string; full_name: string } | null>(null);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetch(`${API_URL}/api/auth/me`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => setUser(data))
        .catch(() => setUser(null));
    }
  }, [pathname]);

  const handleSignOut = () => {
    localStorage.removeItem("token");
    setUser(null);
    router.push("/auth/login");
  };

  const isAuthPage = pathname?.startsWith("/auth");

  if (isAuthPage) return null;

  const menuItems = [
    { name: "Dashboard", icon: <LayoutDashboard size={20} />, path: "/" },
    { name: "Simulation", icon: <PlayCircle size={20} />, path: "/simulate" },
    { name: "History", icon: <History size={20} />, path: "/results" },
    { name: "Analytics", icon: <BarChart3 size={20} />, path: "/analytics" },
    { name: "Settings", icon: <Settings size={20} />, path: "/settings" },
  ];

  return (
    <div className="w-64 bg-[#0f172a] border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 z-50">
      <div className="p-6 flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
          <Box className="text-white" size={24} />
        </div>
        <span className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
          FobSim
        </span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-2">
        {menuItems
          .filter((item) => item.name === "Dashboard" || user)
          .map((item) => (
            <Link
              key={item.path}
              href={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                pathname === item.path
                  ? "bg-gradient-to-r from-cyan-500/10 to-violet-500/10 text-cyan-400 border border-cyan-500/20 shadow-lg shadow-cyan-500/5"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/50"
              }`}
            >
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {item.icon}
              </div>
              <span className="font-medium">{item.name}</span>
            </Link>
          ))}
      </nav>

      <div className="p-4 mt-auto border-t border-slate-800">
        <div className="bg-slate-800/30 rounded-2xl p-4 mb-4">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
              <User size={16} className="text-slate-300" />
            </div>
            <div className="overflow-hidden">
              <p className="text-sm font-semibold text-white truncate">{user ? user.full_name : "Guest User"}</p>
              <p className="text-xs text-slate-500 truncate text-ellipsis">{user ? user.email : "Log in to save results"}</p>
            </div>
          </div>
          {!user && (
            <Link
              href="/auth/login"
              className="w-full py-2 bg-gradient-to-r from-cyan-500 to-violet-600 text-white rounded-lg text-xs font-bold hover:brightness-110 transition flex items-center justify-center gap-2"
            >
              Sign In
            </Link>
          )}
        </div>

        {user && (
          <button
            onClick={handleSignOut}
            className="flex items-center gap-3 w-full px-4 py-2 text-slate-500 hover:text-red-400 transition"
          >
            <LogOut size={18} />
            <span className="font-medium text-sm">Sign Out</span>
          </button>
        )}
      </div>
    </div>
  );
}
