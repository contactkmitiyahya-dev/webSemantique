import { Routes, Route, Link } from "react-router-dom";
import ModulesListe from "./pages/zahra/ModulesListe";
import ModuleFiche from "./pages/zahra/ModuleFiche";
import ModuleForm from "./pages/zahra/ModuleForm";
import CoursListe from "./pages/zahra/CoursListe";
import CoursFiche from "./pages/zahra/CoursFiche";
import CoursForm from "./pages/zahra/CoursForm";
import RessourcesListe from "./pages/zahra/RessourcesListe";
import RessourceFiche from "./pages/zahra/RessourceFiche";
import RessourceForm from "./pages/zahra/RessourceForm";
import Questions from "./pages/zahra/Questions";

export default function App() {
  return (
    <>
      <nav style={{ padding: "12px 24px", borderBottom: "1px solid #ddd" }}>
        <Link to="/modules">Modules</Link>
        <Link to="/cours" style={{ marginLeft: "16px" }}>Cours</Link>
        <Link to="/ressources" style={{ marginLeft: "16px" }}>Ressources</Link>
        <Link to="/questions" style={{ marginLeft: "16px" }}>Questions</Link>
      </nav>
      <Routes>
        <Route path="/modules" element={<ModulesListe />} />
        <Route path="/cours" element={<CoursListe />} />
        <Route path="/cours/nouveau" element={<CoursForm />} />
        <Route path="/cours/:id" element={<CoursFiche />} />
        <Route path="/cours/:id/modifier" element={<CoursForm />} />
        <Route path="/ressources" element={<RessourcesListe />} />
        <Route path="/ressources/nouveau" element={<RessourceForm />} />
        <Route path="/ressources/:id" element={<RessourceFiche />} />
        <Route path="/ressources/:id/modifier" element={<RessourceForm />} />
        <Route path="/questions" element={<Questions />} />
        <Route path="/modules/nouveau" element={<ModuleForm />} />
        <Route path="/modules/:id" element={<ModuleFiche />} />
        <Route path="/modules/:id/modifier" element={<ModuleForm />} />
        <Route
          path="*"
          element={
            <main style={{ padding: "24px", fontFamily: "sans-serif" }}>
              <h1>EduParcours</h1>
              <p>Application en cours de construction.</p>
            </main>
          }
        />
      </Routes>
    </>
  );
}
