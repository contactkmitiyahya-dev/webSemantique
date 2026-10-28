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
    return <div className="loader-wrap"><div className="loader" /></div>;
  }

  return (
    <div className="page-container">
      <Link to={modeEdition ? `/ressources/${id}` : "/ressources"} className="retour">← Retour</Link>
      <div className="page-header">
        <h1 className="page-title">{modeEdition ? "Modifier la ressource" : "Nouvelle ressource"}</h1>
      </div>

      <form onSubmit={soumettre} className="card form-card formulaire">
        <div className="grille-champs">
          <label>
            Intitulé
            <input
              required
              value={valeurs.intitule}
              onChange={(e) => modifier("intitule", e.target.value)}
            />
          </label>

          <label>
            URL
            <input
              type="url"
              required
              value={valeurs.urlRessource}
              onChange={(e) => modifier("urlRessource", e.target.value)}
            />
          </label>

          <label>
            Langue
            <select
              value={valeurs.langue}
              onChange={(e) => modifier("langue", e.target.value)}
            >
              <option value="fr">Français</option>
              <option value="en">Anglais</option>
            </select>
          </label>

          {!modeEdition && (
            <>
              <label>
                Type
                <select
                  value={valeurs.type}
                  onChange={(e) => modifier("type", e.target.value)}
                >
                  {TYPES.map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </label>

              <label>
                Compétence (id)
                <input
                  required
                  placeholder="ex. Comp_HTML"
                  value={valeurs.competenceId}
                  onChange={(e) => modifier("competenceId", e.target.value)}
                />
              </label>

              <label>
                Nombre de pages (optionnel)
                <input
                  type="number"
                  min="1"
                  value={valeurs.nombrePages}
                  onChange={(e) => modifier("nombrePages", e.target.value)}
                />
              </label>

              <label>
                Durée en minutes (optionnel)
                <input
                  type="number"
                  min="1"
                  value={valeurs.dureeMinutes}
                  onChange={(e) => modifier("dureeMinutes", e.target.value)}
                />
              </label>
            </>
          )}

        </div>

        {erreur && <p className="erreur">{erreur}</p>}

        <div className="form-actions">
          <Link to={modeEdition ? `/ressources/${id}` : "/ressources"} className="btn">Annuler</Link>
          <button type="submit" className="btn btn-primary" disabled={enCours}>
            {enCours ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}
