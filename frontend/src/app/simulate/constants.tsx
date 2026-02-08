import React from "react";

// SVG Icons
export const DatabaseIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>
  </svg>
);
export const ComputeIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3M15 1v3M9 20v3M15 20v3M20 9h3M20 14h3M1 9h3M1 14h3"/>
  </svg>
);
export const PaymentIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="1" y="4" width="22" height="16" rx="2"/><path d="M1 10h22"/>
  </svg>
);
export const FingerprintIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M2 12C2 6.5 6.5 2 12 2a10 10 0 0 1 8 4"/><path d="M5 19.5C5.5 18 6 15 6 12c0-.7.12-1.37.34-2"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/>
  </svg>
);

export const BlockchainCubeIcon = () => (
  <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
    <path d="M32 8L52 20V44L32 56L12 44V20L32 8Z" stroke="white" strokeWidth="2" fill="none"/>
    <path d="M32 8V32M32 32L52 20M32 32L12 20M32 32V56M32 32L52 44M32 32L12 44" stroke="white" strokeWidth="1.5" opacity="0.6"/>
    <circle cx="32" cy="8" r="3" fill="white"/><circle cx="52" cy="20" r="3" fill="white"/><circle cx="12" cy="20" r="3" fill="white"/>
    <circle cx="52" cy="44" r="3" fill="white"/><circle cx="12" cy="44" r="3" fill="white"/><circle cx="32" cy="56" r="3" fill="white"/><circle cx="32" cy="32" r="4" fill="white"/>
  </svg>
);

export const CloudLogoAWS = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="currentColor" />
    <path d="M2 17L12 22L22 17V7L12 12L2 7V17Z" fill="currentColor" fillOpacity="0.4" />
  </svg>
);

export const CloudLogoGCP = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
    <path d="M12 7V12L15.5 15.5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
  </svg>
);

export const CloudLogoAzure = () => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
     <path d="M2 14.5L9.5 3L22 21H18.5L12 11.5L8.5 21H2V14.5Z" fill="currentColor" />
  </svg>
);

export const FUNCTIONS = [
  { id: 1, name: "Data Storage", desc: "Secure, decentralized data storage with immutable records.", Icon: DatabaseIcon, color: "#3b82f6" },
  { id: 2, name: "Compute", desc: "Distributed computing for smart contracts.", Icon: ComputeIcon, color: "#8b5cf6" },
  { id: 3, name: "Payment", desc: "Fast digital asset transfers and transactions.", Icon: PaymentIcon, color: "#10b981" },
  { id: 4, name: "Identity", desc: "Decentralized identity and authentication.", Icon: FingerprintIcon, color: "#f59e0b" },
];

export const CONSENSUS = [
  { id: 1, name: "Proof of Work", short: "PoW", color: "#f97316" },
  { id: 2, name: "Proof of Stake", short: "PoS", color: "#22c55e" },
  { id: 3, name: "Proof of Authority", short: "PoA", color: "#3b82f6" },
  { id: 4, name: "Proof of Elapsed Time", short: "PoET", color: "#a855f7" },
  { id: 5, name: "Delegated PoS", short: "DPoS", color: "#ec4899" },
  { id: 6, name: "PBFT", short: "PBFT", color: "#ef4444" },
  { id: 8, name: "Proof of Activity", short: "PoA-H", color: "#06b6d4" },
  { id: 9, name: "Proof of Burn", short: "PoB", color: "#eab308" },
];

export const STEPS = ["Select Functions", "Configure Network", "Simulate Transactions", "Analyze Results"];
