import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";
import RelationSelect from "../../components/RelationSelect";

const NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"];
const VIDE = {
  intitule: "",
  dureeHeures: "",
  niveauDifficulte: "Débutant",
  ordreDansModule: "1",
  moduleId: "",
  formateurId: "",
  competenceId: "",
  technologieId: "",
};

export default function CoursForm() {
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
      .get(`/cours/${id}`)
      .then((res) =>
        setValeurs({
          ...VIDE,
          intitule: res.data.intitule,
          dureeHeures: String(res.data.dureeHeures),
          niveauDifficulte: res.data.niveauDifficulte,
          ordreDansModule: String(res.data.ordreDansModule),
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
      dureeHeures: Number(valeurs.dureeHeures),
      niveauDifficulte: valeurs.niveauDifficulte,
      ordreDansModule: Number(valeurs.ordreDansModule),
    };
    try {
      if (modeEdition) {
        await client.put(`/cours/${id}`, corps);
        navigate(`/cours/${id}`);
      } else {
        const res = await client.post("/cours", {
          ...corps,
          moduleId: valeurs.moduleId,
          formateurId: valeurs.formateurId.trim(),
          competenceId: valeurs.competenceId.trim(),
          technologieId: valeurs.technologieId.trim(),
        });
        navigate(`/cours/${res.data.id}`);
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
      <Link to={modeEdition ? `/cours/${id}` : "/cours"}>← Retour</Link>
      <h1>{modeEdition ? "Modifier le cours" : "Nouveau cours"}</h1>

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
          Durée (heures)
          <input
            type="number"
            required
            min="1"
            value={valeurs.dureeHeures}
            onChange={(e) => modifier("dureeHeures", e.target.value)}
            style={styles.input}
          />
        </label>

        <label style={styles.champ}>
          Niveau
          <select
            value={valeurs.niveauDifficulte}
            onChange={(e) => modifier("niveauDifficulte", e.target.value)}
            style={styles.input}
          >
            {NIVEAUX.map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
        </label>

        <label style={styles.champ}>
          Ordre dans le module
          <input
            type="number"
            required
            min="1"
            value={valeurs.ordreDansModule}
            onChange={(e) => modifier("ordreDansModule", e.target.value)}
            style={styles.input}
          />
        </label>

        {!modeEdition && (
          <>
            <RelationSelect
              endpoint="/modules"
              valeur={valeurs.moduleId}
              onChange={(v) => modifier("moduleId", v)}
              label="Module"
            />

            <label style={styles.champ}>
              Formateur (id)
              <input
                required
                placeholder="ex. Dr_Benali"
                value={valeurs.formateurId}
                onChange={(e) => modifier("formateurId", e.target.value)}
                style={styles.input}
              />
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
              Technologie (id)
              <input
                required
                placeholder="ex. Tech_HTML5"
                value={valeurs.technologieId}
                onChange={(e) => modifier("technologieId", e.target.value)}
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
