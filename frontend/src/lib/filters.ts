export interface Filters {
  minScore: number;
  signal: string;
  sector: string;
  q: string;
}

export const EMPTY_FILTERS: Filters = { minScore: 0, signal: "ALL", sector: "ALL", q: "" };
