import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PositionList from "./pages/PositionList";
import PositionDetail from "./pages/PositionDetail";
import CandidateDetail from "./pages/CandidateDetail";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PositionList />} />
        <Route path="/positions/:id" element={<PositionDetail />} />
        <Route path="/candidates/:id" element={<CandidateDetail />} />
      </Route>
    </Routes>
  );
}
