import { CandlestickSeries, ColorType, LineSeries, LineStyle, createChart } from "lightweight-charts";
import { useEffect, useRef } from "react";
import { useTheme } from "../lib/theme-context";
import type { Bar, SeriesPoint } from "../lib/types";

const CHART_COLORS = {
  dark: {
    up: "#34c98d",
    down: "#f05a50",
    ema20: "#f2b13d",
    ema50: "#7fb4ff",
    sma200: "#8a94a8",
    rsi: "#c9d1e0",
    grid: "#1c2431",
    border: "#232b38",
    text: "#99a3b6",
    crosshair: "#333d4e",
    labelBg: "#1a202b",
  },
  light: {
    up: "#0fa36b",
    down: "#d6453b",
    ema20: "#b45309",
    ema50: "#3b82f6",
    sma200: "#8a94a8",
    rsi: "#475569",
    grid: "#edf0f4",
    border: "#e2e6ed",
    text: "#52617a",
    crosshair: "#c9d0db",
    labelBg: "#f0f2f6",
  },
} as const;

export function PriceChart({
  symbol,
  bars,
  series,
}: {
  symbol: string;
  bars: Bar[];
  series: Record<string, SeriesPoint[]>;
}) {
  const container = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const colors = CHART_COLORS[theme];

  useEffect(() => {
    const el = container.current;
    if (!el || bars.length === 0) return;

    const chart = createChart(el, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: colors.text,
        fontFamily: "'JetBrains Mono', ui-monospace, monospace",
        fontSize: 11,
        panes: {
          separatorColor: colors.border,
          separatorHoverColor: colors.crosshair,
          enableResize: false,
        },
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { color: colors.grid },
      },
      rightPriceScale: { borderColor: colors.border, scaleMargins: { top: 0.08, bottom: 0.08 } },
      timeScale: { borderColor: colors.border, rightOffset: 3, fixLeftEdge: true },
      crosshair: {
        vertLine: { color: colors.crosshair, labelBackgroundColor: colors.labelBg },
        horzLine: { color: colors.crosshair, labelBackgroundColor: colors.labelBg },
      },
      localization: { locale: "id-ID" },
    });

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: colors.up,
      downColor: colors.down,
      wickUpColor: colors.up,
      wickDownColor: colors.down,
      borderVisible: false,
      priceLineVisible: false,
    });
    candles.setData(
      bars.map((b) => ({ time: b.date, open: b.open, high: b.high, low: b.low, close: b.close })),
    );

    const lineDefs = [
      { key: "ema20", color: colors.ema20, width: 2 as const },
      { key: "ema50", color: colors.ema50, width: 1 as const },
      { key: "sma200", color: colors.sma200, width: 1 as const },
    ];
    for (const def of lineDefs) {
      const points = series[def.key] ?? [];
      if (points.length === 0) continue;
      const line = chart.addSeries(LineSeries, {
        color: def.color,
        lineWidth: def.width,
        priceLineVisible: false,
        lastValueVisible: false,
        crosshairMarkerVisible: false,
      });
      line.setData(points.map((p) => ({ time: p.date, value: p.value })));
    }

    const rsiPoints = series.rsi14 ?? [];
    if (rsiPoints.length > 0) {
      const rsi = chart.addSeries(
        LineSeries,
        {
          color: colors.rsi,
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: true,
        },
        1,
      );
      rsi.setData(rsiPoints.map((p) => ({ time: p.date, value: p.value })));
      for (const level of [30, 70]) {
        rsi.createPriceLine({
          price: level,
          color: colors.crosshair,
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: false,
          title: String(level),
        });
      }
      chart.panes()[1]?.setHeight(110);
    }

    chart.timeScale().fitContent();
    return () => chart.remove();
  }, [bars, series, colors, theme]);

  const legend = [
    { key: "ema20", label: "EMA20", color: colors.ema20 },
    { key: "ema50", label: "EMA50", color: colors.ema50 },
    { key: "sma200", label: "SMA200", color: colors.sma200 },
  ].filter((item) => (series[item.key] ?? []).length > 0);

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-line px-1 pb-2 text-[11px] text-muted">
        {legend.map((item) => (
          <span key={item.key} className="inline-flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className="inline-block h-[3px] w-4"
              style={{ background: item.color }}
            />
            {item.label}
          </span>
        ))}
        {(series.rsi14 ?? []).length > 0 ? (
          <span className="inline-flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className="inline-block h-[3px] w-4"
              style={{ background: colors.rsi }}
            />
            RSI14 (panel bawah)
          </span>
        ) : null}
      </div>
      <div
        ref={container}
        role="img"
        aria-label={`Grafik harga ${symbol}, ${bars.length} bar, dengan EMA20, EMA50, SMA200, dan RSI14`}
        className="h-[420px] w-full"
      />
    </div>
  );
}
