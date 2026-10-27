import { Routes, Route, Link, NavLink, useLocation } from "react-router-dom";
import ApprenantsListe  from "./pages/yahya/ApprenantsListe";
import ApprenantFiche   from "./pages/yahya/ApprenantFiche";
import ApprenantForm    from "./pages/yahya/ApprenantForm";
import ApprenantsStats  from "./pages/yahya/ApprenantsStats";
import CertificationsListe from "./pages/yahya/CertificationsListe";
import CertificationForm   from "./pages/yahya/CertificationForm";
import CertificationFiche  from "./pages/yahya/CertificationFiche";
import NlpTester           from "./pages/yahya/NlpTester";
import CompetencesListe    from "./pages/linda/CompetencesListe";
import CompetenceFiche     from "./pages/linda/CompetenceFiche";
import CompetenceForm      from "./pages/linda/CompetenceForm";
import TechnologiesListe   from "./pages/linda/TechnologiesListe";
import TechnologieFiche    from "./pages/linda/TechnologieFiche";
import TechnologieForm     from "./pages/linda/TechnologieForm";
import EvaluationsListe    from "./pages/linda/EvaluationsListe";
import EvaluationFiche     from "./pages/linda/EvaluationFiche";
import EvaluationForm      from "./pages/linda/EvaluationForm";
import QuestionBar         from "./components/QuestionBar";
import "./App.css";

function NavItem({ to, label }) {
  return (
    <NavLink to={to} className={({ isActive }) => "nav-link" + (isActive ? " nav-active" : "")}>
      {label}
    </NavLink>
  );
}

function App() {
  return (
    <div className="app">
      <header className="navbar">
        <Link to="/" className="nav-brand">
          <span className="brand-icon">🎓</span>
          <span>EduParcours</span>
          <span className="brand-tag">Yahya</span>
        </Link>
        <nav className="nav-links">
          <NavItem to="/apprenants"            label="Apprenants" />
          <NavItem to="/apprenants/stats"      label="Statistiques" />
          <NavItem to="/certifications"        label="Certifications" />
          <NavItem to="/competences"           label="Compétences" />
          <NavItem to="/technologies"          label="Technologies" />
          <NavItem to="/evaluations"           label="Évaluations" />
          <NavItem to="/nlp"                   label="NLP" />
        </nav>
      </header>
      <QuestionBar />

      <main className="main-content">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/apprenants"           element={<ApprenantsListe />} />
          <Route path="/apprenants/stats"     element={<ApprenantsStats />} />
          <Route path="/apprenants/nouveau"   element={<ApprenantForm />} />
          <Route path="/apprenants/:id"       element={<ApprenantFiche />} />
          <Route path="/certifications"             element={<CertificationsListe />} />
          <Route path="/certifications/nouvelle"    element={<CertificationForm />} />
          <Route path="/certifications/:id"         element={<CertificationFiche />} />
          <Route path="/nlp"                        element={<NlpTester />} />
          <Route path="/competences"                element={<CompetencesListe />} />
          <Route path="/competences/nouvelle"       element={<CompetenceForm />} />
          <Route path="/competences/:id"            element={<CompetenceFiche />} />
          <Route path="/competences/:id/modifier"   element={<CompetenceForm />} />
          <Route path="/technologies"               element={<TechnologiesListe />} />
          <Route path="/technologies/nouvelle"      element={<TechnologieForm />} />
          <Route path="/technologies/:id"           element={<TechnologieFiche />} />
          <Route path="/technologies/:id/modifier"  element={<TechnologieForm />} />
          <Route path="/evaluations"                element={<EvaluationsListe />} />
          <Route path="/evaluations/nouvelle"       element={<EvaluationForm />} />
          <Route path="/evaluations/:id"            element={<EvaluationFiche />} />
          <Route path="/evaluations/:id/modifier"   element={<EvaluationForm />} />
        </Routes>
      </main>
    </div>
  );
}

function HomePage() {
  return (
    <div className="home">
      <div className="home-hero">
        <div className="hero-icon">🎓</div>
        <h1>Module Apprenants &amp; Certifications</h1>
        <p>Interface de gestion de la tranche Yahya — connectée à Fuseki via FastAPI</p>
        <div className="hero-links">
          <Link to="/apprenants" className="btn btn-primary">Voir les Apprenants</Link>
          <Link to="/certifications" className="btn btn-secondary">Voir les Certifications</Link>
          <Link to="/nlp" className="btn btn-secondary">Tester le NLP 🤖</Link>
        </div>
      </div>
      <div className="feature-grid">
        {[
          { icon:"👤", title:"Apprenants", desc:"CRUD complet, recherche et filtres" },
          { icon:"📊", title:"Statistiques", desc:"Distribution par niveau d'études" },
          { icon:"🏆", title:"Certifications", desc:"Création, attribution aux apprenants" },
          { icon:"🤖", title:"Module NLP", desc:"Questions en langage naturel vers requêtes SPARQL" },
          { icon:"🔗", title:"Relations SPARQL", desc:"Requêtes vers Fuseki en temps réel" },
        ].map(({ icon, title, desc }) => (
          <div key={title} className="feature-card">
            <span className="feature-icon">{icon}</span>
            <h3>{title}</h3>
            <p>{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
