import { createContext, useContext } from "react";

export type Theme = "light" | "dark";

export const ThemeContext = createContext<{ theme: Theme; toggle: () => void }>({
  theme: "dark",
  toggle: () => {},
});

export function initialTheme(): Theme {
  try {
    const stored = window.localStorage.getItem("theme");
    if (stored === "light") return "light";
    return "dark";
  } catch {
    return "dark";
  }
}

export function useTheme() {
  return useContext(ThemeContext);
}
