import os
import base64
import json
import re
from urllib.parse import urlencode
from dotenv import load_dotenv
import requests
from flask import Flask, request, redirect, url_for, session, render_template

if os.getenv("VERCEL") is None:
    load_dotenv()

# Initialize Flask app

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "..", "templates")
)

app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")  # Required for sessions

# Spotify credentials from .env file
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET") #make this dynamic
redirect_uri = os.getenv("REDIRECT_URI")

############################## RETRIEVE USER'S TOP TRACKS FROM PAST 6 MONTHS ##############################

def get_authorization_url():
    auth_url = "https://accounts.spotify.com/authorize"
    scope = "user-library-read user-read-private user-top-read user-read-recently-played playlist-modify-private playlist-modify-public"  # Updated scope
    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "scope": scope,
        "redirect_uri": redirect_uri,
    }
    return f"{auth_url}?{urlencode(auth_params)}"

def get_token(authorization_code):
    url = "https://accounts.spotify.com/api/token"
    client_creds = f"{client_id}:{client_secret}"
    client_creds_b64 = base64.b64encode(client_creds.encode()).decode()
    
    headers = {
        "Authorization": f"Basic {client_creds_b64}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": redirect_uri,
    }
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json().get("access_token")
    print(f"Error exchanging token: {response.status_code}, {response.text}")
    return None


def user_profile(access_token):
    url = "https://api.spotify.com/v1/me"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching user profile: {response.status_code}, {response.text}")
        return None

def user_liked_songs(access_token):
    url = "https://api.spotify.com/v1/me/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    all_tracks = []

    #while loop to retrieve all of the user's liked songs (Spotify can only fetch 50 by itself, so we use pagination handling, which helps us fetch data from multiple pages)
    while url:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            tracks = data.get("items", [])
            
            for item in tracks:
                track = item.get("track")
                if track:  # Ensure the "track" object exists
                    all_tracks.append(track)
            
            # Check if there is another page of results (i.e. more liked songs)
            url = data.get("next")
        else:
            print(f"Error fetching user's liked tracks: {response.status_code}, {response.text}")
            return None

    return all_tracks

def user_top_tracks(access_token):
    url = "https://api.spotify.com/v1/me/top/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"time_range":"medium_term", "limit": 50} #default limit of 50 tracks per request
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["items"]
    else:
        print(f"Error fetching user's top tracks: {response.status_code}, {response.text}")
        return None

 

############################## RETRIEVE ARTIST'S TOP TRACKS FROM PAST 6 MONTHS ##############################

def get_artist_id(access_token, artist_name):
    url = "https://api.spotify.com/v1/search"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    params = {
        "q": artist_name,
        "type": "artist",
        "limit": 50
    }
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        # Try to match exactly with artist_name (ignoring case)
        for artist in data["artists"]["items"]:
            if artist_name.strip().lower() == artist["name"].strip().lower():
                return artist["id"], artist["name"]
        
        print(f"Warning: No exact match found for '{artist_name}', showing first result.")
        # Return the first available result as fallback
        artist = data["artists"]["items"][0]
        return artist["id"], artist["name"]
    else:
        print(f"Error searching for artist: {response.status_code}, {response.text}")
        return None, None

def artist_top_tracks(access_token, artist_id, artist_name):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {"market": "US"}  # Market parameter is required for top-tracks endpoint

    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()["tracks"]
    else:
        print(f"Error fetching {artist_name}'s top tracks: {response.status_code}, {response.text}")
        return None

############################## RETRIEVE SETLIST ##############################

#Enhancement: If no matching playlist is found, return all playlists containing "setlist" and let the user choose manually.
def find_setlist(access_token, artist_name, concert_name=None, year=None):
    # API endpoint; concert_name and year are optional
    search_url = "https://api.spotify.com/v1/search"

    search_parts = [artist_name]
    if concert_name:
        search_parts.append(concert_name)
    search_parts.append("Setlist")
    if year:
        search_parts.append(year)

    params = {
        "q": " ".join(search_parts),
        "type": "playlist",
        "limit": 50
    }

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(search_url, headers=headers, params=params)

    if response.status_code == 200:
        data = response.json()
        playlists = data.get('playlists', {}).get('items', [])

        if not playlists:
            print("No playlists found.")
            return None, None

        name_split = artist_name.lower().split()
        conc_split = (concert_name or "").lower().split()

        # Filter: artist + setlist/concert/tour required; concert and year are optional hints
        # We prioritize matches with concert/year but still return good matches without them
        def matches(playlist):
            if not playlist or not playlist.get('name'):
                return False
            name_lower = playlist['name'].lower()
            # Must have artist name
            if not any(part in name_lower for part in name_split):
                return False
            # Must have setlist/concert/tour keyword
            if 'setlist' not in name_lower and 'concert' not in name_lower and 'tour' not in name_lower:
                return False
            return True

        def score(playlist):
            """Score playlists - higher is better. Prioritize matches with concert/year."""
            if not playlist or not playlist.get('name'):
                return 0
            name_lower = playlist['name'].lower()
            score = 0
            # Bonus for matching concert name (if provided)
            if conc_split:
                for part in conc_split:
                    if part in name_lower:
                        score += 10
            # Bonus for matching year (if provided)
            if year and year in playlist['name']:
                score += 5
            return score

        # Filter to valid playlists
        valid_playlists = [p for p in playlists if matches(p)]
        
        if not valid_playlists:
            print("No playlists match the criteria.")
            return None, None

        # Sort by score (best matches first), then we'll pick the one with most followers
        scored_playlists = [(score(p), p) for p in valid_playlists]
        scored_playlists.sort(reverse=True, key=lambda x: x[0])
        
        # Use top-scored playlists (within top score range) for follower comparison
        if scored_playlists:
            top_score = scored_playlists[0][0]
            # Consider playlists within 5 points of top score
            filtered_playlists = [p for s, p in scored_playlists if s >= max(0, top_score - 5)]
        else:
            filtered_playlists = valid_playlists

        # Find the playlist with the most followers
        most_followed_playlist = None
        max_followers = 0

        for playlist in filtered_playlists:
            playlist_id = playlist['id']
            details_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
            details_response = requests.get(details_url, headers=headers)

            if details_response.status_code == 200:
                details = details_response.json()
                followers = details['followers']['total']
                if followers > max_followers:
                    max_followers = followers
                    most_followed_playlist = {
                        "name": details['name'],
                        "followers": followers,
                        "url": details['external_urls']['spotify'],
                        "id" : playlist_id,
                    }

        if most_followed_playlist:
            print(f"Most followed playlist: {most_followed_playlist['name']}")
            print(f"Saves: {most_followed_playlist['followers']}")
            print(f"URL: {most_followed_playlist['url']}")
        else:
            print("No playlists found.")
            return None, None

        url = f"https://api.spotify.com/v1/playlists/{most_followed_playlist['id']}/tracks"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        response = requests.get(url, headers=headers)
        tracks = response.json()["items"]
        actual_tour_title = most_followed_playlist["name"]
        return tracks, actual_tour_title

    else:
        print(f"Error: {response.status_code}, {response.text}")
        return None, None


############################## COMPARE USER'S LISTENED TRACKS TO ARTIST TRACKS + SETLIST ##############################

# def heard_artist_tracks(tracks):
#     tracks_by_artist = []
#     for track in tracks:
#         if "artists" in track and isinstance(track["artists"], list):
#             artist_names = [a.get("name") for a in track["artists"] if "name" in a]
#             if ARTIST_NAME in artist_names:
#                 tracks_by_artist.append(track)
#     return tracks_by_artist

def track_in_list(track, track_list):
    #this line doesn't consider when the same song is released in diff albums
    #return any(track['uri'] == t.get('uri') for t in track_list) #any is the same as seeing if the track matches any track in the given track_list


    #to check if the consumed track exists in the consumed track_list, we search for any tracks with the same name + artists
    if not track or not isinstance(track, dict):
        return False
    
    name = track.get('name', '').lower().strip()

    artists = {a['name'].lower().strip() for a in track.get('artists', []) if a and a.get('name')}
    
    return any(t['name'].lower().strip() == track['name'].lower().strip() and
               {a['name'].lower().strip() for a in t.get('artists', []) if a and a.get('name')} == artists
               for t in track_list)

def unheard_tracks(user_id, access_token, liked_songs, top_user_tracks, top_artist_tracks, setlist, artist_name, actual_tour_title=None):
    """
    artist_name: must be the looked-up Spotify artist name (never user input).
    actual_tour_title: setlist playlist name when found; never use user's concert/tour input.
    """
    known_songs = liked_songs + [track for track in top_user_tracks if track not in liked_songs]

    # filter tracks + extract URIs only for unknown songs
    unknown_songs_uris = []
    
    # Add artist's top tracks that user hasn't heard
    for i in top_artist_tracks:
        if i and not track_in_list(i, known_songs):
            unknown_songs_uris.append(i['uri'])
                     
    # Add setlist tracks that user hasn't heard
    if setlist:
        for i in setlist:
            track = i.get('track', {})
            if track and not track_in_list(track, known_songs):
                if track.get('uri') not in unknown_songs_uris:
                    unknown_songs_uris.append(track.get('uri'))

    if not unknown_songs_uris:
        return f"No new songs to add! You already know all the songs from {artist_name}'s setlist and top tracks."
    
    # Only use looked-up tour title from setlist; never user input
    if actual_tour_title:
        # Extract year from tour title if present
        year_match = re.search(r'\b(20\d{2})\b', actual_tour_title)
        year_str = f" ({year_match.group(1)})" if year_match else ""
        
        # Clean up the title - remove redundant "Setlist" and artist name if already present
        clean_title = actual_tour_title
        # Remove "Setlist" if present since we'll add "Prep"
        clean_title = re.sub(r'\bSetlist\s*-?\s*', '', clean_title, flags=re.IGNORECASE)
        # Remove artist name if it's at the end
        clean_title = re.sub(rf'\s*-?\s*{re.escape(artist_name)}\s*$', '', clean_title, flags=re.IGNORECASE)
        clean_title = clean_title.strip(' -')
        
        playlist_title = f"{clean_title} Prep"
        
        # Clean description - use clean_title instead of actual_tour_title
        description = f"Songs from {artist_name} you haven't heard yet. Perfect for learning before the show!"
    else:
        playlist_title = f"{artist_name} Concert Prep"
        description = ""

    # Use /me/playlists endpoint for better compatibility
    url = "https://api.spotify.com/v1/me/playlists"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    params = {
        "name": playlist_title,
        "description": description,
        "public": False
    } 

    response = requests.post(url, headers=headers, json=params)
    if response.status_code != 201:
        return f"Error creating playlist: {response.status_code}, {response.text}"

    data = response.json()
    playlist_id = data["id"]
    playlist_url = data["external_urls"]["spotify"]

    # Spotify API allows max 100 tracks per request, so we need to batch them
    playlist_tracks_url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    playlist_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Batch tracks in groups of 100
    batch_size = 100
    for i in range(0, len(unknown_songs_uris), batch_size):
        batch_uris = unknown_songs_uris[i:i + batch_size]
        playlist_params = {"uris": batch_uris}
        playlist_response = requests.post(playlist_tracks_url, headers=playlist_headers, json=playlist_params)
        if playlist_response.status_code not in [200, 201]:
            return f"Error adding tracks to playlist: {playlist_response.status_code}, {playlist_response.text}"
    
    return f"Successfully created playlist with {len(unknown_songs_uris)} songs! Here's the link: {playlist_url}"



# Route to handle logging in
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle form submission - all three fields required
        artist_name = request.form.get('artist_name', '').strip()
        concert_name = request.form.get('concert_name', '').strip()
        year = request.form.get('year', '').strip()
        
        if not artist_name:
            return render_template('index.html', error='Artist name is required.')
        if not concert_name:
            return render_template('index.html', error='Concert/tour name is required.')
        if not year:
            return render_template('index.html', error='Year is required.')
        
        # Store in session for use after redirect
        session['artist_name'] = artist_name
        session['concert_name'] = concert_name
        session['year'] = year

        auth_url = get_authorization_url()
        return redirect(auth_url)
    else:
        # Handle GET request - show form or check for query string (backward compatibility)
        info = request.args.get("info", "")
        if info:
            # Backward compatibility: ?info=artist/concert/year
            parts = [p.strip() for p in info.split("/")]
            if len(parts) >= 3 and parts[0] and parts[1] and parts[2]:
                session['artist_name'] = parts[0]
                session['concert_name'] = parts[1]
                session['year'] = parts[2]
                auth_url = get_authorization_url()
                return redirect(auth_url)
            else:
                return render_template('index.html', error='All three fields required: artist, concert, and year (e.g. ?info=Artist/Concert/2024).')
        
        # Show the form
        return render_template('index.html')


    
# Route to handle the redirect URI after user authorizes
@app.route('/redirect')
def redirect_page():
    authorization_code = request.args.get('code')
    if not authorization_code:
        return render_template('result.html', error='Authorization code missing. Please try again.')

    access_token = get_token(authorization_code)
    if not access_token:
        return render_template('result.html', error='Error retrieving access token. Please check your CLIENT_SECRET in the .env file.')

    user_prof = user_profile(access_token)
    if not user_prof:
        return render_template('result.html', error='Error retrieving user profile.')

    liked_songs = user_liked_songs(access_token)
    if not liked_songs:
        return render_template('result.html', error='Error retrieving user\'s liked songs.')
    
    top_user_tracks = user_top_tracks(access_token)
    if not top_user_tracks:
        return render_template('result.html', error='Error retrieving user\'s top tracks.')
    
    # Retrieve artist/concert info from session
    artist_name = session.get('artist_name')
    concert_name = session.get('concert_name') or ''
    year = session.get('year') or ''
    
    if not artist_name:
        return render_template('result.html', error='Session expired. Please start over and enter an artist name.')
    
    artist_id = get_artist_id(access_token, artist_name)
    if not artist_id or not artist_id[0]:
        return render_template('result.html', error=f'Error retrieving artist\'s ID. Could not find "{artist_name}".')
    artist_id_value = artist_id[0]
    actual_artist_name = artist_id[1]  # Use the actual Spotify artist name
    
    top_artist_tracks = artist_top_tracks(access_token, artist_id_value, actual_artist_name)
    if not top_artist_tracks:
        return render_template('result.html', error='Error retrieving artist\'s top tracks.')
   
    setlist_result = find_setlist(access_token, actual_artist_name, concert_name or None, year or None)
    setlist_tracks = None
    actual_tour_title = None
    if setlist_result[0] is not None:
        setlist_tracks, actual_tour_title = setlist_result

    playlist_result = ""
    playlist_url = None

    if setlist_tracks is not None:
        playlist_result = unheard_tracks(user_prof["id"], access_token, liked_songs, top_user_tracks, top_artist_tracks, setlist_tracks, actual_artist_name, actual_tour_title=actual_tour_title)
        print(playlist_result)
    else:
        # No setlist: use only looked-up artist name, no tour title (never user input)
        playlist_result = unheard_tracks(user_prof["id"], access_token, liked_songs, top_user_tracks, top_artist_tracks, [], actual_artist_name)
        print(playlist_result)

    # Extract playlist URL from result if it contains one
    if playlist_result:
        # Try multiple patterns to extract the URL
        url_patterns = [
            r'https://open\.spotify\.com/playlist/[a-zA-Z0-9]+',
            r'https://open\.spotify\.com/playlist/[^\s]+',
        ]
        for pattern in url_patterns:
            url_match = re.search(pattern, playlist_result)
            if url_match:
                playlist_url = url_match.group(0)
                break
        
        # Also try splitting by common phrases
        if not playlist_url:
            for phrase in ["Here's the link:", "link:", "Link:"]:
                if phrase in playlist_result:
                    try:
                        potential_url = playlist_result.split(phrase)[1].strip().split()[0]
                        if potential_url.startswith('http'):
                            playlist_url = potential_url
                            break
                    except:
                        pass

    # Only use looked-up values for display; never user input
    display_artist_name = actual_artist_name
    display_tour = actual_tour_title if actual_tour_title else "No setlist found"

    return render_template('result.html',
        artist_name=display_artist_name,
        tour_name=display_tour,
        liked_songs_count=len(liked_songs),
        user_top_tracks_count=len(top_user_tracks),
        artist_top_tracks_count=len(top_artist_tracks),
        setlist_found=setlist_tracks is not None,
        setlist_tracks_count=len(setlist_tracks) if setlist_tracks else 0,
        playlist_result=playlist_result,
        playlist_url=playlist_url
    )


# For Vercel serverless deployment
app = app