"use client";

export const getApiUrl = () => {
  // Check for the production environment variable first
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }

  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // Handle both development and production scenarios
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return "http://localhost:8000";
    }
    // Fallback for IP-based access
    return `http://${hostname}:8000`;
  }
  return "http://localhost:8000";
};

export const API_URL = getApiUrl();
