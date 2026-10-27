import { Routes, Route, Link, NavLink, useLocation } from "react-router-dom";
import ApprenantsListe  from "./pages/yahya/ApprenantsListe";
import ApprenantFiche   from "./pages/yahya/ApprenantFiche";
import ApprenantForm    from "./pages/yahya/ApprenantForm";
import ApprenantsStats  from "./pages/yahya/ApprenantsStats";
import CertificationsListe from "./pages/yahya/CertificationsListe";
import CertificationForm   from "./pages/yahya/CertificationForm";
import CertificationFiche  from "./pages/yahya/CertificationFiche";
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
        </nav>
      </header>

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
        </div>
      </div>
      <div className="feature-grid">
        {[
          { icon:"👤", title:"Apprenants", desc:"CRUD complet, recherche et filtres" },
          { icon:"📊", title:"Statistiques", desc:"Distribution par niveau d'études" },
          { icon:"🏆", title:"Certifications", desc:"Création, attribution aux apprenants" },
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
