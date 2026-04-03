"use client";

export const getApiUrl = () => {
  // 1. Try the baked-in build-time variable
  let url = process.env.NEXT_PUBLIC_API_URL;

  // 2. If missing, look for it in the window object (if we inject it later)
  if (!url && typeof window !== 'undefined' && (window as any)._env_?.NEXT_PUBLIC_API_URL) {
    url = (window as any)._env_.NEXT_PUBLIC_API_URL;
  }

  // 3. Ensure the URL has a protocol and is NOT pointing to the frontend itself
  if (url) {
    if (!url.startsWith("http://") && !url.startsWith("https://")) {
      url = `https://${url}`;
    }
    // Remove trailing slash if present
    return url.replace(/\/$/, "");
  }

  // 4. Final Fallback for Local vs Production
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return "http://localhost:8000";
    }
    
    // IMPORTANT: If we are on Render but NEXT_PUBLIC_API_URL is missing,
    // we default to the predictable Render naming convention
    const backendHost = hostname.replace('frontend', 'backend');
    return `https://${backendHost}`;
  }
  
  return "http://localhost:8000";
};

export const API_URL = getApiUrl();
