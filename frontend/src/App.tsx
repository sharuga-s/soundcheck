import React, { useState } from 'react';
import ColorBends from './ColorBends';
import './App.css';

function App() {
  const [artistName, setArtistName] = useState('');
  const [concertName, setConcertName] = useState('');
  const [year, setYear] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!artistName) {
      setError('Artist name is required.');
      return;
    }
    if (!concertName && !year) {
      setError('Please also enter a concert/tour name or year.');
      return;
    }

    // Redirect to Flask backend
    const formData = new URLSearchParams();
    formData.append('artist_name', artistName);
    formData.append('concert_name', concertName);
    formData.append('year', year);

    window.location.href = `http://localhost:5001/?${formData.toString()}`;
  };

  return (
    <div className="app">
      <ColorBends
        className="background"
        colors={['#1a1a1a', '#2d2d2d', '#404040']}
        speed={0.15}
        rotation={0}
        autoRotate={2}
        scale={1.5}
        frequency={0.8}
        warpStrength={0.6}
        mouseInfluence={0.2}
        parallax={0.3}
        noise={0.02}
        transparent={false}
      />
      
      <div className="container">
        <h1>soundcheck</h1>
        <p className="subtitle">Learn the setlist before you show up.</p>
        
        {error && <div className="error">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="artist_name">Artist Name *</label>
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
              Concert / Tour Name <span className="optional">optional</span>
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
              Year <span className="optional">optional</span>
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