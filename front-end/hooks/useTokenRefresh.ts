// hooks/useTokenRefresh.ts
import { useEffect, useRef } from "react";
import api from "../lib/api"; // Ensure your axios instance has withCredentials enabled

const DEFAULT_REFRESH_INTERVAL_MS = 1 * 60 * 60 * 1000; // 1 hour (fallback)
const INITIAL_DELAY_MS = 5000; // Delay before the first attempt (5 seconds)

export function useTokenRefresh() {
  // A ref to store the current timer so we can cancel it if needed
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Helper to schedule the next refresh attempt after a certain delay
  const scheduleRefresh = (delay: number) => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = setTimeout(refreshToken, delay);
  };

  // Function that calls the refresh endpoint
  const refreshToken = async () => {
    try {
      console.log("Attempting token refresh...");
      const response = await api.post("/refresh");
      console.log("Token refresh check complete:", response.data);

      // If the backend indicates that the refresh interval hasn't been met,
      // schedule the next call based on the provided timestamp.
      if (response.data.refresh_success === false) {
        const nextAllowed = response.data.next_refresh_allowed_at;
        const now = Date.now(); // current time in ms
        // Assume nextAllowed is in seconds; convert to ms
        const nextAllowedMs = nextAllowed * 1000;
        const delay = Math.max(nextAllowedMs - now, 10000); // fallback to at least 10 sec delay
        console.log(
          `Refresh not performed. Scheduling next attempt in ${delay} ms.`
        );
        scheduleRefresh(delay);
      } else {
        // Refresh was successful, schedule the next refresh after the default interval.
        console.log("Token refreshed successfully. Scheduling next refresh.");
        scheduleRefresh(DEFAULT_REFRESH_INTERVAL_MS);
      }
    } catch (error: any) {
      console.error(
        "Token refresh failed:",
        error.response?.data || error.message
      );
      if (error.response?.status === 401) {
        console.error(
          "Refresh failed (401), session likely expired or invalid."
        );
        // Optionally, force logout or display a message to the user
        // window.location.href = '/login';
      }
      // In case of error, retry again after a fallback delay (e.g., 30 seconds)
      scheduleRefresh(30000);
    }
  };

  useEffect(() => {
    // Begin the token refresh cycle after an initial delay
    const initialTimer = setTimeout(refreshToken, INITIAL_DELAY_MS);
    return () => {
      clearTimeout(initialTimer);
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);
}
