/** Message lisible a partir d'une erreur Axios ({"detail": "..."} renvoye par FastAPI). */
export function messageErreur(err, defaut = "Une erreur est survenue.") {
  if (!err.response) return "L'API ne répond pas (http://localhost:8000).";
  const detail = err.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join(" ; ");
  return defaut;
}

/** 2026-11-12T00:00:00 -> 12/11/2026 */
export function formaterDate(iso) {
  if (!iso) return "—";
  const [a, m, j] = iso.slice(0, 10).split("-");
  return `${j}/${m}/${a}`;
}

export function aujourdhui() {
  return new Date().toISOString().slice(0, 10);
}
