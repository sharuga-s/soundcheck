import { useState, useMemo } from 'react';
import ColorBends from './ColorBends';
import './App.css';

function App() {
  const [artistName, setArtistName] = useState('');
  const [concertName, setConcertName] = useState('');
  const [year, setYear] = useState('');
  const [error, setError] = useState('');

  // Memoize the colors array so it doesn't change on every render
  const backgroundColors = useMemo(() => ['#0a4d3c', '#1a6b54', '#2d8c6d', '#3fad85'], []);

  const handleSubmit = (e: any) => {
    e.preventDefault();
    
    if (!artistName) {
      setError('Artist name is required.');
      return;
    }
    if (!concertName && !year) {
      setError('Please enter a concert/tour name or year.');
      return;
    }

    const formData = new URLSearchParams();
    formData.append('artist_name', artistName);
    formData.append('concert_name', concertName);
    formData.append('year', year);

    // Use relative URL so it works in both local and production
    window.location.href = `/api/?${formData.toString()}`;
  };

  return (
    <div className="app">
      <ColorBends
        className="background"
        colors={backgroundColors}
        speed={0.2}
        rotation={45}
        autoRotate={10}
        scale={1.2}
        frequency={1.2}
        warpStrength={1.0}
        mouseInfluence={0.5}
        parallax={0.5}
        noise={0.03}
      />
      
      <div className="container">
        <h1>soundcheck</h1>
        <p className="subtitle">Learn the setlist before you show up.</p>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="artist_name">ARTIST NAME *</label>
            <input
              type="text"
              id="artist_name"
              value={artistName}
              onChange={(e) => setArtistName(e.target.value)}
              placeholder="Taylor Swift"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="concert_name">
              CONCERT / TOUR NAME <span className="optional">optional</span>
            </label>
            <input
              type="text"
              id="concert_name"
              value={concertName}
              onChange={(e) => setConcertName(e.target.value)}
              placeholder="The Eras Tour"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="year">
              YEAR <span className="optional">optional</span>
            </label>
            <input
              type="text"
              id="year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="2024"
            />
          </div>
          
          <button type="submit" className="submit-btn">
            Create Playlist
          </button>
        </form>
      </div>
    </div>
  );
}

export default App;