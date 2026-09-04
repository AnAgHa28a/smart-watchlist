const GOOD = "#0ca30c";
const CRITICAL = "#e66767";
const MUTED = "#52514e";

export default function Sparkline({
  values, width = 100, height = 28, surfaceColor = "#111826",
}: { values: number[]; width?: number; height?: number; surfaceColor?: string }) {
  if (!values || values.length < 2) {
    return <div style={{ width, height }} className="flex items-center justify-center text-[10px] text-slate-700">—</div>;
  }

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const padY = 3;

  const points = values.map((v, i) => {
    const x = (i / (values.length - 1)) * width;
    const y = height - padY - ((v - min) / range) * (height - padY * 2);
    return [x, y] as const;
  });

  const netUp = values[values.length - 1] >= values[0];
  const lineColor = netUp ? GOOD : CRITICAL;
  const pathD = points.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
  const [lastX, lastY] = points[points.length - 1];

  const areaD = `${pathD} L${width},${height} L0,${height} Z`;

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
      <path d={areaD} fill={lineColor} opacity={0.08} />
      <path d={pathD} fill="none" stroke={MUTED} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round" opacity={0.55} />
      <path
        d={points.slice(-Math.ceil(points.length / 4)).map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ")}
        fill="none" stroke={lineColor} strokeWidth={2} strokeLinejoin="round" strokeLinecap="round"
      />
      <circle cx={lastX} cy={lastY} r={4} fill={lineColor} stroke={surfaceColor} strokeWidth={2} />
    </svg>
  );
}
