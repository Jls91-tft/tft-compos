/* Cliente de la API de DivisionUp.
   El frontend llama a /api/... y nginx hace proxy al backend FastAPI.
   El Riot ID (opcional) se guarda en localStorage y se adjunta a las peticiones;
   en modo mock del backend se ignora. */
const API = {
  base: "/api",

  riotId() { return localStorage.getItem("synapse_riot_id") || ""; },
  setRiotId(v) { localStorage.setItem("synapse_riot_id", (v || "").trim()); },
  lang() {
    const saved = localStorage.getItem("synapse_lang");
    if (saved) return saved;
    return (navigator.language || "es").toLowerCase().indexOf("en") === 0 ? "en" : "es";
  },

  _q(params) {
    const p = new URLSearchParams(params);
    const r = this.riotId();
    if (r) p.set("riot_id", r);
    return p.toString();
  },

  async _err(res) {
    let detail;
    try { detail = (await res.json()).detail; } catch { detail = res.statusText; }
    return new Error(detail || ("Error " + res.status));
  },
  async _get(path) {
    const res = await fetch(this.base + path);
    if (!res.ok) throw await this._err(res);
    return res.json();
  },
  async _post(path, body) {
    const res = await fetch(this.base + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw await this._err(res);
    return res.json();
  },

  matches(game) { return this._get(`/coaching/matches?${this._q({ game })}`); },
  analyzed(game) { return this._get(`/coaching/analyzed/${game}?${this._q({})}`); },
  rank(game) { return this._get(`/coaching/rank/${game}?${this._q({})}`); },
  report(game, id, regenerate = false) { return this._get(`/coaching/report/${game}/${encodeURIComponent(id)}?${this._q({ lang: this.lang(), regenerate })}`); },
  plan(game, regenerate = false) { return this._get(`/coaching/plan/${game}?${this._q({ lang: this.lang(), regenerate })}`); },
  stats(game) { return this._get(`/stats?${this._q({ game })}`); },
  meta(game) { return this._get(`/meta?game=${game}`); },
  chat(game, id, question) {
    return this._post(`/chat`, { game, match_id: id, question, riot_id: this.riotId(), lang: this.lang() });
  },
  labExplorer(game, kind) { return this._get(`/lab/explorer?game=${game}&kind=${kind}`); },
  labRecipes() { return this._get(`/lab/recipes`); },
  labGpi(game) { return this._get(`/lab/gpi?game=${game}`); },
  labChampion(id) { return this._get(`/lab/champion?id=${encodeURIComponent(id || "mago-control")}`); },
};
