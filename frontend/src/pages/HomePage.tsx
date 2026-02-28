import { useState } from "react";
import { useNavigate } from "react-router-dom";
import rabbitLogo from "../assets/rabbit-logo.png";
import "./HomePage.css";

export function HomePage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/results?q=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="home">
      <div className="home__header-wrap">
        <header className="home__header">
          <div className="home__brand">
            RabbitHole
            <img src={rabbitLogo} alt="Logo" className="home__logo" />
          </div>
          <button type="button" className="home__settings-btn">
            Settings
          </button>
        </header>
      </div>

      <main className="home__main">
        <div className="home__content">
          <p className="home__intro">
            Search papers and explore a knowledge graph of citations and
            relevance.
          </p>

          <form onSubmit={handleSubmit} className="home__form">
            <input
              type="text"
              placeholder="Search by title, keywords,..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="home__search-input"
            />
            <div className="home__form-row">
              <span className="home__example">E.g: "phasor"</span>
              <button type="submit" className="home__submit-btn">
                Search
              </button>
            </div>
          </form>

          <div className="home__graph-placeholder" />
        </div>
      </main>

      <footer className="home__footer">RabbitHole</footer>
    </div>
  );
}
