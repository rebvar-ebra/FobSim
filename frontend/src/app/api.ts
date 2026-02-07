"use client";

export const getApiUrl = () => {
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    // Handle both development and production scenarios
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return "http://localhost:8000";
    }
    return `http://${hostname}:8000`;
  }
  return "http://localhost:8000";
};

export const API_URL = getApiUrl();
