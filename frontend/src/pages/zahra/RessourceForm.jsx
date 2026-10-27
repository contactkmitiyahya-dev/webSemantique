import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";

const TYPES = [
  "TutorielComplet", "SupportPDF", "GuideRapide", "Diapositives",
  "DocumentationOfficielle", "EditeurEnLigne", "DocumentReference", "Video", "Webinaire",
];
const VIDE = {
  intitule: "",
  urlRessource: "",
  langue: "fr",
  type: "Video",
  competenceId: "",
  nombrePages: "",
  dureeMinutes: "",
};

export default function RessourceForm() {
  const { id } = useParams();
  const modeEdition = Boolean(id);
  const navigate = useNavigate();
  const [valeurs, setValeurs] = useState(VIDE);
  const [chargement, setChargement] = useState(modeEdition);
  const [enCours, setEnCours] = useState(false);
  const [erreur, setErreur] = useState("");

  useEffect(() => {
    if (!modeEdition) return;
    client
      .get(`/ressources/${id}`)
      .then((res) =>
        setValeurs({
          ...VIDE,
          intitule: res.data.label,
          urlRessource: res.data.urlRessource,
          langue: res.data.langue,
        })
      )
      .catch((e) => setErreur(e.message))
      .finally(() => setChargement(false));
  }, [id, modeEdition]);

  function modifier(champ, valeur) {
    setValeurs((precedent) => ({ ...precedent, [champ]: valeur }));
  }

  async function soumettre(e) {
    e.preventDefault();
    setErreur("");
    setEnCours(true);
    const corps = {
      intitule: valeurs.intitule.trim(),
      urlRessource: valeurs.urlRessource.trim(),
      langue: valeurs.langue,
    };
    try {
      if (modeEdition) {
        await client.put(`/ressources/${id}`, corps);
        navigate(`/ressources/${id}`);
      } else {
        const creation = {
          ...corps,
          type: valeurs.type,
          competenceId: valeurs.competenceId.trim(),
        };
        if (valeurs.nombrePages) creation.nombrePages = Number(valeurs.nombrePages);
        if (valeurs.dureeMinutes) creation.dureeMinutes = Number(valeurs.dureeMinutes);
        const res = await client.post("/ressources", creation);
        navigate(`/ressources/${res.data.id}`);
      }
    } catch (err) {
      setErreur(err.message);
      setEnCours(false);
    }
  }

  if (chargement) {
    return <main style={styles.page}><p>Chargement...</p></main>;
  }

  return (
    <main style={styles.page}>
      <Link to={modeEdition ? `/ressources/${id}` : "/ressources"}>← Retour</Link>
      <h1>{modeEdition ? "Modifier la ressource" : "Nouvelle ressource"}</h1>

      <form onSubmit={soumettre} style={styles.form}>
        <label style={styles.champ}>
          Intitulé
          <input
            required
            value={valeurs.intitule}
            onChange={(e) => modifier("intitule", e.target.value)}
            style={styles.input}
          />
        </label>

        <label style={styles.champ}>
          URL
          <input
            type="url"
            required
            value={valeurs.urlRessource}
            onChange={(e) => modifier("urlRessource", e.target.value)}
            style={styles.input}
          />
        </label>

        <label style={styles.champ}>
          Langue
          <select
            value={valeurs.langue}
            onChange={(e) => modifier("langue", e.target.value)}
            style={styles.input}
          >
            <option value="fr">Français</option>
            <option value="en">Anglais</option>
          </select>
        </label>

        {!modeEdition && (
          <>
            <label style={styles.champ}>
              Type
              <select
                value={valeurs.type}
                onChange={(e) => modifier("type", e.target.value)}
                style={styles.input}
              >
                {TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>

            <label style={styles.champ}>
              Compétence (id)
              <input
                required
                placeholder="ex. Comp_HTML"
                value={valeurs.competenceId}
                onChange={(e) => modifier("competenceId", e.target.value)}
                style={styles.input}
              />
            </label>

            <label style={styles.champ}>
              Nombre de pages (optionnel)
              <input
                type="number"
                min="1"
                value={valeurs.nombrePages}
                onChange={(e) => modifier("nombrePages", e.target.value)}
                style={styles.input}
              />
            </label>

            <label style={styles.champ}>
              Durée en minutes (optionnel)
              <input
                type="number"
                min="1"
                value={valeurs.dureeMinutes}
                onChange={(e) => modifier("dureeMinutes", e.target.value)}
                style={styles.input}
              />
            </label>
          </>
        )}

        {erreur && <p style={styles.erreur}>{erreur}</p>}

        <button type="submit" disabled={enCours}>
          {enCours ? "Enregistrement..." : "Enregistrer"}
        </button>
      </form>
    </main>
  );
}

const styles = {
  page: { padding: "24px", fontFamily: "sans-serif" },
  form: { display: "flex", flexDirection: "column", gap: "16px", maxWidth: "420px" },
  champ: { display: "flex", flexDirection: "column", gap: "6px", fontSize: "14px" },
  input: { padding: "8px", fontSize: "14px", borderRadius: "6px", border: "1px solid #ccc" },
  erreur: { color: "#e53e3e" },
};
