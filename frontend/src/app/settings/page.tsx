"use client";

import React from "react";
import Link from "next/link";
import { Sliders, Shield, User, Globe, ArrowRight } from "lucide-react";

const SETTINGS_CARDS = [
  {
    title: "Advanced Parameters",
    desc: "Fine-tune core simulation variables, gossip intervals, and blockchain physics.",
    icon: Sliders,
    href: "/settings/parameters",
    color: "cyan"
  },
  {
    title: "Security & Access",
    desc: "Manage authentication tokens, session persistence, and API permissions.",
    icon: Shield,
    href: "/settings",
    disabled: true
  },
  {
    title: "Cloud Credentials",
    desc: "Provisioning keys for AWS, GCP, and Azure integration.",
    icon: Globe,
    href: "/settings",
    disabled: true
  },
  {
    title: "User Profile",
    desc: "Update personal information, avatar, and notification preferences.",
    icon: User,
    href: "/settings",
    disabled: true
  }
];

export default function SettingsHub() {
  return (
    <div className="max-w-5xl mx-auto space-y-12 pb-20">
      <div>
        <h1 className="text-4xl font-extrabold text-white">System Settings</h1>
        <p className="text-slate-400 mt-2 text-lg">Configure your research environment and platform preferences.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {SETTINGS_CARDS.map((card) => {
          const Content = (
            <div className={`p-8 rounded-[2rem] bg-slate-900 border border-slate-800 transition-all duration-300 group relative overflow-hidden ${
              card.disabled ? 'opacity-60 cursor-not-allowed' : 'hover:border-cyan-500/30 hover:bg-slate-900/80 cursor-pointer shadow-xl'
            }`}>
              {!card.disabled && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-cyan-500/5 blur-[50px] rounded-full translate-x-1/2 -translate-y-1/2 group-hover:bg-cyan-500/10 transition" />
              )}

              <div className="flex items-start gap-5 relative z-10">
                <div className="w-14 h-14 rounded-2xl bg-slate-800 flex items-center justify-center group-hover:scale-110 transition duration-300 shadow-inner">
                  <card.icon size={28} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white group-hover:text-cyan-400 transition">{card.title}</h3>
                    {card.disabled && <span className="text-[10px] font-bold bg-slate-800 text-slate-500 px-2 py-0.5 rounded-full uppercase tracking-widest">Planned</span>}
                  </div>
                  <p className="text-slate-500 mt-2 text-sm leading-relaxed">{card.desc}</p>
                </div>
                {!card.disabled && (
                  <ArrowRight size={20} className="text-slate-700 group-hover:text-white transition group-hover:translate-x-1" />
                )}
              </div>
            </div>
          );

          return card.disabled ? (
            <div key={card.title}>{Content}</div>
          ) : (
            <Link key={card.title} href={card.href}>
              {Content}
            </Link>
          );
        })}
      </div>

      <div className="p-10 rounded-[2.5rem] bg-gradient-to-br from-[#0f1021] to-slate-900 border border-slate-800 text-center">
         <h3 className="text-xl font-bold text-white mb-2">Need help with configuration?</h3>
         <p className="text-slate-400 mb-6 max-w-lg mx-auto">Refer to the Research Documentation for detailed explanations of each parameter's physical impact.</p>
         <button className="px-8 py-3 bg-slate-800 text-white rounded-xl font-bold hover:bg-slate-700 transition">
            View Documentation
         </button>
      </div>
    </div>
  );
}
