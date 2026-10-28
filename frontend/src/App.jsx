// Cadre de l'application : navigation par domaine, barre de question, thème, accueil, routes.
import { useEffect, useState } from 'react'
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import client from './api/client'
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
import CompetencesListe from './pages/linda/CompetencesListe'
import CompetenceFiche from './pages/linda/CompetenceFiche'
import CompetenceForm from './pages/linda/CompetenceForm'
import TechnologiesListe from './pages/linda/TechnologiesListe'
import TechnologieFiche from './pages/linda/TechnologieFiche'
import TechnologieForm from './pages/linda/TechnologieForm'
import EvaluationsListe from './pages/linda/EvaluationsListe'
import EvaluationFiche from './pages/linda/EvaluationFiche'
import EvaluationForm from './pages/linda/EvaluationForm'
import ModulesListe from './pages/zahra/ModulesListe'
import ModuleFiche from './pages/zahra/ModuleFiche'
import ModuleForm from './pages/zahra/ModuleForm'
import CoursListe from './pages/zahra/CoursListe'
import CoursFiche from './pages/zahra/CoursFiche'
import CoursForm from './pages/zahra/CoursForm'
import RessourcesListe from './pages/zahra/RessourcesListe'
import RessourceFiche from './pages/zahra/RessourceFiche'
import RessourceForm from './pages/zahra/RessourceForm'
import Questions from './pages/zahra/Questions'
import QuestionBar from './components/QuestionBar'
import './App.css'

// Navigation par domaine (et non par membre). « classe » : classe de l'ontologie affichée à côté,
// « api » : route qui donne le total sur l'accueil, « membre » : auteur de la page (en petit sous le lien).
const DOMAINES = [
  {
    titre: 'Offre de formation',
    liens: [
      { to: '/formations', membre: 'Imem', texte: 'Formations', classe: 'Formation', api: 'formations' },
      { to: '/parcours', membre: 'Imem', texte: 'Parcours', classe: 'Parcours', api: 'parcours' },
      { to: '/modules', membre: 'Zahra', texte: 'Modules', classe: 'Module', api: 'modules' },
      { to: '/cours', membre: 'Zahra', texte: 'Cours', classe: 'Cours', api: 'cours' },
      { to: '/ressources', membre: 'Zahra', texte: 'Ressources', classe: 'RessourcePedagogique', api: 'ressources' },
    ],
  },
  {
    titre: 'Apprenants',
    liens: [
      { to: '/apprenants', membre: 'Yahya', texte: 'Apprenants', classe: 'Apprenant', api: 'apprenants' },
      { to: '/apprenants/stats', membre: 'Yahya', texte: 'Statistiques' },
      { to: '/certifications', membre: 'Yahya', texte: 'Certifications', classe: 'Certification', api: 'certifications' },
    ],
  },
  {
    titre: 'Compétences',
    liens: [
      { to: '/competences', membre: 'Linda', texte: 'Compétences', classe: 'Competence', api: 'competences' },
      { to: '/technologies', membre: 'Linda', texte: 'Technologies', classe: 'Technologie', api: 'technologies' },
      { to: '/evaluations', membre: 'Linda', texte: 'Évaluations', classe: 'Evaluation', api: 'evaluations' },
    ],
  },
  {
    titre: 'Acteurs',
    liens: [
      { to: '/formateurs', membre: 'Ala', texte: 'Formateurs', classe: 'Formateur', api: 'formateurs' },
      { to: '/personnel', membre: 'Ala', texte: 'Personnel', classe: 'PersonnelAdministratif', api: 'responsables' },
      { to: '/organismes', membre: 'Ala', texte: 'Organismes', classe: 'Organisme', api: 'organismes' },
      { to: '/domaines', membre: 'Ala', texte: 'Domaines', classe: 'Domaine', api: 'domaines' },
    ],
  },
  {
    titre: 'Explorer',
    liens: [
      { to: '/recherche', membre: 'Imem', texte: 'Recherche globale' },
      { to: '/nlp', membre: 'Yahya', texte: 'Question en français' },
      { to: '/questions', membre: 'Zahra', texte: 'Questions guidées' },
    ],
  },
]
const TOUS_LES_LIENS = DOMAINES.flatMap((d) => d.liens)

// Lien actif = le plus long chemin du menu qui préfixe l'URL (/apprenants/stats ne rallume pas /apprenants)
function lienActif(pathname) {
  return TOUS_LES_LIENS
    .filter((l) => pathname === l.to || pathname.startsWith(`${l.to}/`))
    .sort((a, b) => b.to.length - a.to.length)[0]?.to
}

// ------------------------------------------------------------------ thème
const THEMES = [
  { valeur: 'system', texte: 'Auto' },
  { valeur: 'light', texte: 'Clair' },
  { valeur: 'dark', texte: 'Sombre' },
]

function lireTheme() {
  try {
    const t = localStorage.getItem('eduparcours-theme')
    return t === 'light' || t === 'dark' ? t : 'system'
  } catch {
    return 'system'
  }
}

function useTheme() {
  const [theme, setTheme] = useState(lireTheme)
  useEffect(() => {
    const racine = document.documentElement
    if (theme === 'system') delete racine.dataset.theme
    else racine.dataset.theme = theme
    try {
      if (theme === 'system') localStorage.removeItem('eduparcours-theme')
      else localStorage.setItem('eduparcours-theme', theme)
    } catch { /* stockage indisponible : le choix vaut pour cette visite */ }
  }, [theme])
  return [theme, setTheme]
}

// ------------------------------------------------------------------ navigation
function Navigation({ theme, setTheme }) {
  const { pathname } = useLocation()
  const actif = lienActif(pathname)
  const [api, setApi] = useState('attente')

  useEffect(() => {
    client.get('/sante').then(() => setApi('ok')).catch(() => setApi('ko'))
  }, [])

  return (
    <nav className="nav" aria-label="Navigation principale">
      <Link to="/" className="marque">
        <span className="marque-nom">Edu<em>Parcours</em></span>
        <span className="marque-sous">Registre des formations</span>
      </Link>

      <div className="nav-groupes">
        {DOMAINES.map((d) => (
          <div key={d.titre} className="nav-groupe">
            <span className="nav-titre">{d.titre}</span>
            {d.liens.map((l) => (
              <NavLink key={l.to} to={l.to} className={() => (l.to === actif ? 'active' : '')}
                       aria-current={l.to === actif ? 'page' : undefined}>
                <span className="nav-texte">
                  {l.texte}
                  {l.membre && <span className="nav-membre">{l.membre}</span>}
                </span>
                {l.classe && <span className="nav-classe">{l.classe}</span>}
              </NavLink>
            ))}
          </div>
        ))}
      </div>

      <div className="nav-pied">
        <span className={`etat-api ${api}`}>
          {api === 'ok' ? 'API · Fuseki connectés' : api === 'ko' ? 'API injoignable (port 8000)' : 'Connexion à l’API…'}
        </span>
        <div className="theme-choix" role="group" aria-label="Thème">
          {THEMES.map((t) => (
            <button key={t.valeur} type="button" aria-pressed={theme === t.valeur} onClick={() => setTheme(t.valeur)}>
              {t.texte}
            </button>
          ))}
        </div>
      </div>
    </nav>
  )
}

// ------------------------------------------------------------------ accueil
function Accueil() {
  const [totaux, setTotaux] = useState({})

  useEffect(() => {
    TOUS_LES_LIENS.filter((l) => l.api).forEach((l) => {
      client.get(`/${l.api}`, { params: { taille: 100 } })
        .then((r) => {
          const d = r.data
          const n = typeof d?.total === 'number' ? d.total : Array.isArray(d?.donnees) ? d.donnees.length
            : Array.isArray(d) ? d.length : null
          setTotaux((t) => ({ ...t, [l.api]: n }))
        })
        .catch(() => setTotaux((t) => ({ ...t, [l.api]: null })))
    })
  }, [])

  return (
    <div>
      <header className="accueil-entete">
        <div>
          <div className="surtitre">PREFIX edu: &lt;http://www.eduparcours.org/ontologie#&gt;</div>
          <h1>Registre EduParcours</h1>
          <p>
            Formations, parcours, compétences et apprenants, décrits par une ontologie OWL et interrogés
            en SPARQL. Posez une question en français dans la barre du haut, ou ouvrez une classe ci-dessous.
          </p>
        </div>
        <div className="actions">
          <Link to="/formations/nouvelle" className="btn primaire">Nouvelle formation</Link>
          <Link to="/recherche" className="btn">Recherche globale</Link>
        </div>
      </header>

      <div className="domaines">
        {DOMAINES.filter((d) => d.liens.some((l) => l.api)).map((d) => (
          <section key={d.titre} className="domaine">
            <h2>{d.titre}</h2>
            <div className="classes">
              {d.liens.filter((l) => l.api).map((l) => {
                const n = totaux[l.api]
                return (
                  <Link key={l.to} to={l.to} className="classe">
                    <span className={`classe-nombre ${n == null ? 'inconnu' : ''}`}>
                      {n === undefined ? '…' : n === null ? '—' : n}
                    </span>
                    <span className="classe-nom">{l.texte}</span>
                    <span className="classe-uri">edu:{l.classe}</span>
                  </Link>
                )
              })}
            </div>
          </section>
        ))}
      </div>
    </div>
  )
}

// Route d'une partie pas encore intégrée (ex. lien vers /cours/X depuis une fiche)
function NonDisponible() {
  const { pathname } = useLocation()
  return (
    <div className="non-disponible">
      <h1>Page introuvable</h1>
      <p className="doux">L’adresse <code>{pathname}</code> ne correspond à aucune page du registre.</p>
      <Link to="/" className="btn">Retour à l’accueil</Link>
    </div>
  )
}

// ------------------------------------------------------------------ cadre
function Cadre() {
  const [theme, setTheme] = useTheme()
  const [menuOuvert, setMenuOuvert] = useState(false)
  const { pathname } = useLocation()

  // Sur mobile, le menu se referme après chaque navigation
  useEffect(() => { setMenuOuvert(false) }, [pathname])

  return (
    <div className={`app ${menuOuvert ? 'menu-ouvert' : ''}`}>
      <Navigation theme={theme} setTheme={setTheme} />
      {menuOuvert && <div className="voile" onClick={() => setMenuOuvert(false)} />}

      <div className="principal">
        <div className="barre-haut">
          <button type="button" className="bouton-menu" onClick={() => setMenuOuvert(true)} aria-label="Ouvrir le menu">
            Menu
          </button>
          {/* Barre de question NLP (Linda), présente sur toutes les pages */}
          <QuestionBar />
        </div>

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
            <Route path="/competences" element={<CompetencesListe />} />
            <Route path="/competences/nouvelle" element={<CompetenceForm />} />
            <Route path="/competences/:id" element={<CompetenceFiche />} />
            <Route path="/competences/:id/modifier" element={<CompetenceForm />} />
            <Route path="/technologies" element={<TechnologiesListe />} />
            <Route path="/technologies/nouvelle" element={<TechnologieForm />} />
            <Route path="/technologies/:id" element={<TechnologieFiche />} />
            <Route path="/technologies/:id/modifier" element={<TechnologieForm />} />
            <Route path="/evaluations" element={<EvaluationsListe />} />
            <Route path="/evaluations/nouvelle" element={<EvaluationForm />} />
            <Route path="/evaluations/:id" element={<EvaluationFiche />} />
            <Route path="/evaluations/:id/modifier" element={<EvaluationForm />} />
            <Route path="/modules" element={<ModulesListe />} />
            <Route path="/modules/nouveau" element={<ModuleForm />} />
            <Route path="/modules/:id" element={<ModuleFiche />} />
            <Route path="/modules/:id/modifier" element={<ModuleForm />} />
            <Route path="/cours" element={<CoursListe />} />
            <Route path="/cours/nouveau" element={<CoursForm />} />
            <Route path="/cours/:id" element={<CoursFiche />} />
            <Route path="/cours/:id/modifier" element={<CoursForm />} />
            <Route path="/ressources" element={<RessourcesListe />} />
            <Route path="/ressources/nouveau" element={<RessourceForm />} />
            <Route path="/ressources/:id" element={<RessourceFiche />} />
            <Route path="/ressources/:id/modifier" element={<RessourceForm />} />
            <Route path="/questions" element={<Questions />} />
            <Route path="*" element={<NonDisponible />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Cadre />
    </BrowserRouter>
  )
}
