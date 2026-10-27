// TEMPORAIRE (Ala) – à remplacer par la version de Yahya (React Router, menu, accueil)
// Seules les routes d'Ala sont branchées ; les autres membres ajouteront les leurs.
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import FormateursListe from './pages/ala/FormateursListe'
import FormateurFiche from './pages/ala/FormateurFiche'
import PersonnelListe from './pages/ala/PersonnelListe'
import OrganismesListe from './pages/ala/OrganismesListe'
import OrganismeFiche from './pages/ala/OrganismeFiche'
import DomainesListe from './pages/ala/DomainesListe'
import FormationsCatalogue from './pages/imem/FormationsCatalogue'
import FormationFiche from './pages/imem/FormationFiche'
import FormationForm from './pages/imem/FormationForm'
import ParcoursListe from './pages/imem/ParcoursListe'
import ParcoursFiche from './pages/imem/ParcoursFiche'
import ParcoursForm from './pages/imem/ParcoursForm'
import RechercheGlobale from './pages/imem/RechercheGlobale'
import ApprenantsListe from './pages/yahya/ApprenantsListe'
import ApprenantFiche from './pages/yahya/ApprenantFiche'
import ApprenantForm from './pages/yahya/ApprenantForm'
import ApprenantsStats from './pages/yahya/ApprenantsStats'
import CertificationsListe from './pages/yahya/CertificationsListe'
import CertificationForm from './pages/yahya/CertificationForm'
import CertificationFiche from './pages/yahya/CertificationFiche'
import NlpTester from './pages/yahya/NlpTester'
import './App.css'

// Menu : une entrée par membre
const MENU = [
  {
    membre: 'Yahya',
    liens: [
      { to: '/apprenants', texte: 'Apprenants' },
      { to: '/apprenants/stats', texte: 'Statistiques' },
      { to: '/certifications', texte: 'Certifications' },
      { to: '/nlp', texte: 'Question (NLP)' },
    ],
  },
  {
    membre: 'Ala',
    liens: [
      { to: '/formateurs', texte: 'Formateurs' },
      { to: '/personnel', texte: 'Personnel' },
      { to: '/organismes', texte: 'Organismes' },
      { to: '/domaines', texte: 'Domaines' },
    ],
  },
  {
    membre: 'Imem',
    liens: [
      { to: '/formations', texte: 'Formations' },
      { to: '/parcours', texte: 'Parcours' },
      { to: '/recherche', texte: 'Recherche globale' },
    ],
  },
]

function Accueil() {
  return (
    <div>
      <h1>EduParcours</h1>
      <p>Projet Web sémantique – thématique Éducation et Formation.</p>
      <p className="doux">React (5173) → FastAPI (8000) → Fuseki (3030). Choisissez une rubrique dans le menu.</p>
    </div>
  )
}

// Route d'un autre membre pas encore fusionnée (ex. /cours/Cours_React depuis une fiche)
function NonDisponible() {
  const { pathname } = useLocation()
  return (
    <div>
      <h1>Page non disponible</h1>
      <p>La page <code>{pathname}</code> appartient à une autre partie du projet et n'est pas encore intégrée.</p>
      <Link to="/">← Accueil</Link>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="mise-en-page">
        <nav className="menu">
          <Link to="/" className="logo">EduParcours</Link>
          {MENU.map((groupe) => (
            <div key={groupe.membre} className="menu-groupe">
              <span className="menu-membre">{groupe.membre}</span>
              {groupe.liens.map((l) => <NavLink key={l.to} to={l.to}>{l.texte}</NavLink>)}
            </div>
          ))}
        </nav>
        <main className="contenu">
          <Routes>
            <Route path="/" element={<Accueil />} />
            <Route path="/formateurs" element={<FormateursListe />} />
            <Route path="/formateurs/:id" element={<FormateurFiche />} />
            <Route path="/personnel" element={<PersonnelListe />} />
            <Route path="/organismes" element={<OrganismesListe />} />
            <Route path="/organismes/:id" element={<OrganismeFiche />} />
            <Route path="/domaines" element={<DomainesListe />} />
            <Route path="/formations" element={<FormationsCatalogue />} />
            <Route path="/formations/nouvelle" element={<FormationForm />} />
            <Route path="/formations/:id" element={<FormationFiche />} />
            <Route path="/formations/:id/modifier" element={<FormationForm />} />
            <Route path="/parcours" element={<ParcoursListe />} />
            <Route path="/parcours/nouveau" element={<ParcoursForm />} />
            <Route path="/parcours/:id" element={<ParcoursFiche />} />
            <Route path="/parcours/:id/modifier" element={<ParcoursForm />} />
            <Route path="/recherche" element={<RechercheGlobale />} />
            <Route path="/apprenants" element={<ApprenantsListe />} />
            <Route path="/apprenants/stats" element={<ApprenantsStats />} />
            <Route path="/apprenants/nouveau" element={<ApprenantForm />} />
            <Route path="/apprenants/:id" element={<ApprenantFiche />} />
            <Route path="/certifications" element={<CertificationsListe />} />
            <Route path="/certifications/nouvelle" element={<CertificationForm />} />
            <Route path="/certifications/:id" element={<CertificationFiche />} />
            <Route path="/nlp" element={<NlpTester />} />
            <Route path="*" element={<NonDisponible />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
