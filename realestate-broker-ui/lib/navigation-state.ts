"use client";

import * as React from "react";
import { usePathname } from "next/navigation";

export type RouteMatchState = "inactive" | "self" | "descendant";

export function normalizePath(path?: string | null): string {
  if (!path) {
    return "/";
  }

  // Strip query string and hash fragments to ensure consistent comparisons
  let normalized = path.split("?")[0]?.split("#")[0] ?? "/";

  if (!normalized.startsWith("/")) {
    normalized = `/${normalized}`;
  }

  if (normalized.length > 1) {
    normalized = normalized.replace(/\/+$/g, "");
    if (normalized === "") {
      normalized = "/";
    }
  }

  return normalized;
}

export function getRouteMatchState(
  targetHref: string,
  currentPathname: string
): RouteMatchState {
  const target = normalizePath(targetHref);
  const current = normalizePath(currentPathname);

  if (current === target) {
    return "self";
  }

  if (target === "/") {
    return current === "/" ? "self" : "descendant";
  }

  if (current.startsWith(`${target}/`)) {
    return "descendant";
  }

  return "inactive";
}

export function usePersistentPathname(): string {
  const pathname = usePathname();
  const initialRef = React.useRef<string | null>(null);

  if (initialRef.current === null) {
    initialRef.current = normalizePath(
      typeof window !== "undefined" ? window.location.pathname : pathname
    );
  }

  const [activePath, setActivePath] = React.useState<string>(
    initialRef.current
  );

  React.useEffect(() => {
    setActivePath(normalizePath(pathname));
  }, [pathname]);

  return activePath;
}
