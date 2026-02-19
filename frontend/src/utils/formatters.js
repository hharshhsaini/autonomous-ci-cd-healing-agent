export const formatTime = (seconds) => {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m === 0) return `${s}s`;
  return `${m}m ${s}s`;
};

export const formatScore = (score) => score?.total ?? 0;

export const formatBranch = (name) => name || "—";

export const formatDate = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { 
    year: "numeric", 
    month: "short", 
    day: "numeric" 
  });
};

export const formatTimeShort = (iso) => {
  const d = new Date(iso);
  return d.toLocaleTimeString("en-US", { hour12: false });
};

export const formatPercent = (value) => {
  return `${Math.round(value)}%`;
};
