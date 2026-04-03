"use client";

export const getApiUrl = () => {
  let url = process.env.NEXT_PUBLIC_API_URL;

  // If provided, ensure it has a protocol
  if (url) {
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }
    return url;
  }

  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // Handle both development and production scenarios
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return "http://localhost:8000";
    }
    // Fallback: Default to HTTPS for remote environments if protocol is unknown
    return `https://${hostname}:8000`;
  }
  return "http://localhost:8000";
};

export const API_URL = getApiUrl();
