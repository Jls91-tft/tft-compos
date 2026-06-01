/* Gráficas en SVG puro (sin librerías). Consumen el formato que devuelve la API:
   evol = {min,max,invert,suffix,points:[{label,value}]}
   dist = {bars:[{label,value,color}]}
   table = {cols:[...], rows:[[...]]} */
const CHART_COLORS = { good: "#3FB950", warn: "#E3B341", bad: "#F85149", gold: "#E3B341", accent: "#8B5CF6", muted: "#8B949E" };

function renderLineChart(hostId, evol) {
  const W = 480, H = 200, padL = 40, padR = 14, padT = 16, padB = 30;
  const { min, max, invert, suffix = "", points = [] } = evol || {};
  const n = points.length || 1;
  const px = (i) => padL + (i * (W - padL - padR) / Math.max(n - 1, 1));
  const py = (v) => { let t = (v - min) / ((max - min) || 1); if (!invert) t = 1 - t; return padT + t * (H - padT - padB); };
  let g = "";
  [min, (min + max) / 2, max].forEach((t) => {
    const y = py(t);
    g += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="#2A2F3A" stroke-width="1"/>`;
    g += `<text x="${padL - 7}" y="${y + 3}" class="ax-lbl" text-anchor="end">${Math.round(t * 10) / 10}${suffix}</text>`;
  });
  const line = points.map((d, i) => `${px(i)},${py(d.value)}`).join(" ");
  g += `<polygon points="${padL},${H - padB} ${line} ${W - padR},${H - padB}" fill="#8B5CF6" fill-opacity="0.10"/>`;
  g += `<polyline points="${line}" fill="none" stroke="#8B5CF6" stroke-width="2.5" stroke-linejoin="round"/>`;
  points.forEach((d, i) => {
    g += `<circle cx="${px(i)}" cy="${py(d.value)}" r="3.5" fill="#0D1117" stroke="#8B5CF6" stroke-width="2"/>`;
    g += `<text x="${px(i)}" y="${H - padB + 16}" class="ax-lbl" text-anchor="middle">${d.label}</text>`;
  });
  document.getElementById(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${g}</svg>`;
}

function renderBarChart(hostId, dist) {
  const W = 480, H = 200, padL = 30, padR = 10, padT = 18, padB = 30;
  const bars = (dist && dist.bars) || [];
  const n = bars.length || 1, maxV = Math.max(1, ...bars.map((b) => b.value));
  const bw = (W - padL - padR) / n, barW = bw * 0.58;
  let g = "";
  bars.forEach((b, i) => {
    const h = (b.value / maxV) * (H - padT - padB);
    const x = padL + i * bw + (bw - barW) / 2, y = H - padB - h;
    const col = CHART_COLORS[b.color] || "#8B5CF6";
    g += `<rect x="${x}" y="${y}" width="${barW}" height="${h}" rx="3" fill="${col}" fill-opacity="0.85"/>`;
    g += `<text x="${x + barW / 2}" y="${y - 5}" class="bar-val" text-anchor="middle">${b.value}</text>`;
    g += `<text x="${x + barW / 2}" y="${H - padB + 16}" class="ax-lbl" text-anchor="middle">${b.label}</text>`;
  });
  document.getElementById(hostId).innerHTML = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${g}</svg>`;
}

function renderTable(hostId, table) {
  const cols = (table && table.cols) || [], rows = (table && table.rows) || [];
  let h = `<table class="stat-table"><thead><tr>` +
    cols.map((c, i) => `<th${i > 0 ? ' class="num"' : ""}>${c}</th>`).join("") +
    `</tr></thead><tbody>`;
  rows.forEach((r) => { h += `<tr>` + r.map((c, i) => `<td${i > 0 ? ' class="num"' : ""}>${c}</td>`).join("") + `</tr>`; });
  document.getElementById(hostId).innerHTML = h + `</tbody></table>`;
}
