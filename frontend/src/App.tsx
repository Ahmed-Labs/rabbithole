import { useState } from "react";
import { HomePage } from "./pages/HomePage";
import { ResultsPage } from "./pages/ResultsPage";
import "./App.css";

type View = "home" | "results";

function App() {
  const [currentView, setCurrentView] = useState<View>("home");
  const [searchQuery, setSearchQuery] = useState("");

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentView("results");
  };

  const handleNewSearch = () => {
    setCurrentView("home");
    setSearchQuery("");
  };

  return (
    <>
      {currentView === "home" && <HomePage onSearch={handleSearch} />}
      {currentView === "results" && (
        <ResultsPage searchQuery={searchQuery} onNewSearch={handleNewSearch} />
      )}
    </>
  );
}

export default App;
