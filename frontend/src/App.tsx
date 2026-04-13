import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import PositionList from "./pages/PositionList";
import PositionDetail from "./pages/PositionDetail";
import CandidateComparison from "./pages/CandidateComparison";
import CandidateDetail from "./pages/CandidateDetail";
import InterviewLive from "./pages/InterviewLive";
import InterviewSummary from "./pages/InterviewSummary";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/positions" replace />} />
        <Route path="/positions" element={<PositionList />} />
        <Route path="/positions/:id" element={<PositionDetail />} />
        <Route path="/positions/:id/compare" element={<CandidateComparison />} />
        <Route path="/candidates/:id" element={<CandidateDetail />} />
        <Route path="/interviews/:id/live" element={<InterviewLive />} />
        <Route path="/interviews/:id/summary" element={<InterviewSummary />} />
      </Route>
    </Routes>
  );
}
