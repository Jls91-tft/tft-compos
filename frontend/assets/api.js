/* Cliente de la API de DivisionUp (beta TFT).
   El frontend llama a /api/... y nginx hace proxy al backend FastAPI.
   El Riot ID se guarda en localStorage (clave divisionup_riot_id; se migra
   automáticamente desde la clave antigua synapse_riot_id si existe). */
const API = {
  base: "/api",

  riotId() {
    let v = localStorage.getItem("divisionup_riot_id");
    if (!v) {
      // migración silenciosa desde el diseño anterior
      v = localStorage.getItem("synapse_riot_id") || "";
      if (v) localStorage.setItem("divisionup_riot_id", v);
    }
    return v || "";
  },
  setRiotId(v) { localStorage.setItem("divisionup_riot_id", (v || "").trim()); },

  _q(params) {
    const p = new URLSearchParams(params);
    const r = this.riotId();
    if (r) p.set("riot_id", r);
    return p.toString();
  },

  async _err(res) {
    let detail;
    try { detail = (await res.json()).detail; } catch { detail = res.statusText; }
    return new Error(typeof detail === "string" ? detail : ("Error " + res.status));
  },
  async _get(path) {
    const res = await fetch(this.base + path);
    if (!res.ok) throw await this._err(res);
    return res.json();
  },
  async _send(method, path, body) {
    const res = await fetch(this.base + path, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) throw await this._err(res);
    return res.json();
  },

  /* --- núcleo de análisis (FASE 4) --- */
  matches() { return this._get(`/matches?${this._q({})}`); },
  report(matchId) { return this._get(`/report/${encodeURIComponent(matchId)}?${this._q({})}`); },
  feedback(matchId, patronId, voto) {
    return this._send("POST", `/feedback?${this._q({})}`, { match_id: matchId, patron_id: patronId, voto });
  },
  objective() { return this._get(`/objective?${this._q({})}`); },
  rank() { return this._get(`/rank?${this._q({})}`); },
  deleteAccount() { return this._send("DELETE", `/account?${this._q({})}`); },

  /* --- complementos --- */
  stats(game = "tft") { return this._get(`/stats?${this._q({ game })}`); },
  meta(game = "tft") { return this._get(`/meta?game=${game}`); },
  waitlist(datos) { return this._send("POST", `/waitlist`, datos); },
};
