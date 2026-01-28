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
    
    // Check all required fields
    const missingFields = [];
    if (!artistName.trim()) missingFields.push('Artist Name');
    if (!concertName.trim()) missingFields.push('Concert / Tour Name');
    if (!year.trim()) missingFields.push('Year');
    
    if (missingFields.length > 0) {
      setError('Please fill in ' + missingFields.join(', ') + ' before submitting.');
      return;
    }

    // Create a form and submit it as POST to the API
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/api/';
    
    const addField = (name: string, value: string) => {
      const input = document.createElement('input');
      input.type = 'hidden';
      input.name = name;
      input.value = value;
      form.appendChild(input);
    };
    
    addField('artist_name', artistName);
    addField('concert_name', concertName);
    addField('year', year);
    
    document.body.appendChild(form);
    form.submit();
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
            <label htmlFor="concert_name">CONCERT / TOUR NAME *</label>
            <input
              type="text"
              id="concert_name"
              value={concertName}
              onChange={(e) => setConcertName(e.target.value)}
              placeholder="The Eras Tour"
              required
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="year">YEAR *</label>
            <input
              type="text"
              id="year"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="2024"
              required
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