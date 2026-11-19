"use client";

import { useEffect } from "react";

export function HydrationComplete() {
  useEffect(() => {
    window.dispatchEvent(new Event("keyzone:hydrated"));
  }, []);
  return null;
}
