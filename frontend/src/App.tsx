import { Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { ResultsPage } from "./pages/ResultsPage";
import { FlowPage } from "./pages/FlowPage";
function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/results" element={<ResultsPage />} />
      <Route path="/flow" element={<FlowPage />} />
    </Routes>
  );
}

export default App;
