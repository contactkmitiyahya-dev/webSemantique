import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import client from "../../api/client";
import RelationSelect from "../../components/RelationSelect";

const NIVEAUX = ["Débutant", "Intermédiaire", "Avancé"];
const VIDE = { intitule: "", dureeHeures: "", niveauDifficulte: "Débutant", prerequisId: "" };

export default function ModuleForm() {
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
      .get(`/modules/${id}`)
      .then((res) =>
        setValeurs({
          intitule: res.data.intitule,
          dureeHeures: String(res.data.dureeHeures),
          niveauDifficulte: res.data.niveauDifficulte,
          prerequisId: "",
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
    };
    try {
      if (modeEdition) {
        await client.put(`/modules/${id}`, corps);
        navigate(`/modules/${id}`);
      } else {
        const res = await client.post("/modules", {
          ...corps,
          prerequisId: valeurs.prerequisId || null,
        });
        navigate(`/modules/${res.data.id}`);
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
      <Link to={modeEdition ? `/modules/${id}` : "/modules"} className="retour">← Retour</Link>
      <div className="page-header">
        <h1 className="page-title">{modeEdition ? "Modifier le module" : "Nouveau module"}</h1>
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
            Durée (heures)
            <input
              type="number"
              required
              min="1"
              value={valeurs.dureeHeures}
              onChange={(e) => modifier("dureeHeures", e.target.value)}
            />
          </label>

          <label>
            Niveau
            <select
              value={valeurs.niveauDifficulte}
              onChange={(e) => modifier("niveauDifficulte", e.target.value)}
            >
              {NIVEAUX.map((n) => (
                <option key={n} value={n}>{n}</option>
              ))}
            </select>
          </label>

          {!modeEdition && (
            <RelationSelect
              endpoint="/modules"
              valeur={valeurs.prerequisId}
              onChange={(v) => modifier("prerequisId", v)}
              label="Prérequis (optionnel)"
            />
          )}

        </div>

        {erreur && <p className="erreur">{erreur}</p>}

        <div className="form-actions">
          <Link to={modeEdition ? `/modules/${id}` : "/modules"} className="btn">Annuler</Link>
          <button type="submit" className="btn btn-primary" disabled={enCours}>
            {enCours ? "Enregistrement..." : "Enregistrer"}
          </button>
        </div>
      </form>
    </div>
  );
}
