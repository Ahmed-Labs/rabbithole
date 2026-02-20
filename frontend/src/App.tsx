import { useState } from "react";
import { HomePage } from "./pages/HomePage";
import { ResultsPage } from "./pages/ResultsPage";
import { FlowPage } from "./pages/FlowPage";
import type { AnalysisOptions } from "./components/PaperPreview";
import "./App.css";

type View = "home" | "results" | "flow";

function App() {
  const [currentView, setCurrentView] = useState<View>("home");
  const [searchQuery, setSearchQuery] = useState("");
  const [analysisOptions, setAnalysisOptions] =
    useState<AnalysisOptions | null>(null);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentView("results");
  };

  const handleNewSearch = () => {
    setCurrentView("home");
    setSearchQuery("");
  };

  const handleAnalyze = (options: AnalysisOptions) => {
    setAnalysisOptions(options);
    setCurrentView("flow");
  };

  return (
    <>
      {currentView === "home" && <HomePage onSearch={handleSearch} />}
      {currentView === "results" && (
        <ResultsPage
          searchQuery={searchQuery}
          onNewSearch={handleNewSearch}
          onAnalyze={handleAnalyze}
        />
      )}
      {currentView === "flow" && (
        <FlowPage onBack={() => setCurrentView("results")} />
      )}
    </>
  );
}

export default App;
