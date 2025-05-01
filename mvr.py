import streamlit as st
import requests
import difflib
from typing import List

# TMDB API configuration
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]  # Load API key from Streamlit secrets
if not TMDB_API_KEY:
    st.error("TMDB API key not found in Streamlit secrets.")
    st.stop()

BASE_URL = "https://api.themoviedb.org/3"
SEARCH_URL = f"{BASE_URL}/search/movie"
GENRE_URL = f"{BASE_URL}/genre/movie/list"
DISCOVER_URL = f"{BASE_URL}/discover/movie"

def recommend_movie(query, api_key):  # Changed from search_movie
    params = {
        'api_key': api_key,
        'query': query
    }
    response = requests.get(SEARCH_URL, params=params)
    if response.status_code == 200:
        results = response.json()['results']
        for movie in results:
            movie['genre_ids'] = movie.get('genre_ids', [])
        return results
    else:
        st.error(f"Error fetching recommendations: {response.status_code}")  # Changed error message
        return []

def get_movie_suggestions(query, api_key):
    # Fetch movie suggestions based on the query
    params = {
        'api_key': api_key,
        'query': query
    }
    response = requests.get(SEARCH_URL, params=params)
    if response.status_code == 200:
        return [movie['title'] for movie in response.json()['results']]
    else:
        st.error(f"Error fetching recommendations: {response.status_code}")  # Changed error message
        return []

def get_genres(api_key):
    params = {
        'api_key': api_key
    }
    response = requests.get(GENRE_URL, params=params)
    if response.status_code == 200:
        return {genre['id']: genre['name'] for genre in response.json()['results']}
    return {}

def get_recommendations_by_genre(movie_id, genre_ids, api_key):
    params = {
        'api_key': api_key,
        'with_genres': ','.join(map(str, genre_ids)),
        'sort_by': 'popularity.desc',
        'page': 1
    }
    response = requests.get(DISCOVER_URL, params=params)
    if response.status_code == 200:
        return response.json()['results'][:5]  # Return top 5 recommendations
    return []

def get_movie_titles(api_key) -> List[str]:
    """Fetch a list of popular movie titles for autocorrection"""
    popular_movies_url = f"{BASE_URL}/movie/popular"
    titles = []
    # Fetch first 5 pages of popular movies
    for page in range(1, 6):
        params = {
            'api_key': api_key,
            'page': page
        }
        response = requests.get(popular_movies_url, params=params)
        if response.status_code == 200:
            movies = response.json().get('results', [])
            titles.extend(movie['title'] for movie in movies)
    return titles

def autocorrect_movie_name(input_name: str, movie_titles: List[str]) -> str:
    """Autocorrect the input movie name using difflib"""
    if not input_name:
        return input_name
    
    # Find close matches
    matches = difflib.get_close_matches(input_name, movie_titles, n=1, cutoff=0.6)
    
    if matches:
        suggested_name = matches[0]
        # If the suggested name is different from input, show the suggestion
        if suggested_name.lower() != input_name.lower():
            if st.button(f"Did you mean: {suggested_name}?"):
                return suggested_name
    return input_name

def get_genre_list(api_key):
    """Fetch all available movie genres"""
    params = {'api_key': api_key}
    response = requests.get(GENRE_URL, params=params)
    if response.status_code == 200:
        genres = response.json().get('genres', [])
        return {genre['id']: genre['name'] for genre in genres}
    return {}

def get_recommendations_by_genres(genre_ids, api_key, page=1):
    """Get recommendations based on specific genres"""
    params = {
        'api_key': api_key,
        'with_genres': ','.join(map(str, genre_ids)),
        'sort_by': 'vote_average.desc',
        'vote_count.gte': 1000,  # Ensure quality recommendations
        'page': page
    }
    response = requests.get(DISCOVER_URL, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def get_region_recommendations(api_key, region=None, page=1):
    """Get recommendations from specific regions/industries"""
    params = {
        'api_key': api_key,
        'sort_by': 'popularity.desc',
        'vote_count.gte': 100,
        'page': page,
        'language': 'en'  # Keep English as display language
    }
    
    if region:
        params['region'] = region
        params['with_original_language'] = {
            'IN': 'hi',  # Hindi (Bollywood)
            'KR': 'ko',  # Korean
            'JP': 'ja',  # Japanese
            'HK': 'zh',  # Chinese
            'FR': 'fr',  # French
            'ES': 'es'   # Spanish
        }.get(region, 'en')
    
    response = requests.get(DISCOVER_URL, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def recommend_person(query, api_key):  # Changed from search_person
    """Recommend an actor/actress"""  # Updated docstring
    person_search_url = f"{BASE_URL}/search/person"
    params = {
        'api_key': api_key,
        'query': query
    }
    response = requests.get(person_search_url, params=params)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

def get_person_movies(person_id, api_key):
    """Get movies for a specific actor/actress"""
    person_movies_url = f"{BASE_URL}/person/{person_id}/movie_credits"
    params = {
        'api_key': api_key
    }
    response = requests.get(person_movies_url, params=params)
    if response.status_code == 200:
        return response.json().get('cast', [])
    return []

def display_actor_movies(person_id, person_name, api_key):
    """Display movies for a given actor ID"""
    movies = get_person_movies(person_id, TMDB_API_KEY)
    
    # Filter and sort movies by popularity
    filtered_movies = [
        movie for movie in movies
        if movie.get('poster_path') and movie.get('release_date')
    ]
    filtered_movies.sort(key=lambda x: x.get('popularity', 0), reverse=True)
    
    if filtered_movies:
        st.subheader(f"Movies featuring {person_name}")
        
        # Create table for actor's movies
        actor_movies_html = "<table style='width:100%;'><tr>"
        actor_movies_html += "<th>Image</th><th>Title</th><th>Character</th><th>Release Date</th><th>Vote Average</th><th>Overview</th></tr>"
        
        for movie in filtered_movies[:10]:  # Show top 10 movies
            actor_movies_html += "<tr>"
            actor_movies_html += f"<td><img src='https://image.tmdb.org/t/p/w200{movie['poster_path']}' style='width:150px;'/></td>"
            actor_movies_html += f"<td>{movie['title']}</td>"
            actor_movies_html += f"<td>{movie.get('character', 'N/A')}</td>"
            actor_movies_html += f"<td>{movie['release_date']}</td>"
            actor_movies_html += f"<td>{movie.get('vote_average', 'N/A'):.1f}</td>"
            actor_movies_html += f"<td>{movie.get('overview', '')[:100]}...</td>"
            actor_movies_html += "</tr>"
        
        actor_movies_html += "</table>"
        st.markdown(actor_movies_html, unsafe_allow_html=True)
        return filtered_movies
    else:
        st.write("No movies found for this actor/actress.")
        return []

# Ensure this function is defined to fetch movie titles
@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_movie_titles():
    return get_movie_titles(TMDB_API_KEY)

# Initialize movie_titles before using it
movie_titles = get_cached_movie_titles()

st.title("Movie Recommendation System")
st.markdown("**Created by ΉΛЯƧΉ BΛJPΛY**")

# Create main navigation tabs
tab_movie, tab_actor, tab_genre = st.tabs([
    "🎬 Recommend by Movie", 
    "🎭 Recommend by Actor", 
    "🎪 Browse by Genre"
])

# Movie Search Tab
with tab_movie:
    st.header("Recommend Movies")
    movie_name = st.text_input("Enter a movie name:", key="movie_recommend")
    
    if movie_name:
        # Apply autocorrection
        corrected_movie_name = autocorrect_movie_name(movie_name, movie_titles)
        
        if corrected_movie_name != movie_name:
            st.info(f"Recommending for: {corrected_movie_name}")
        
        movies = recommend_movie(corrected_movie_name, TMDB_API_KEY)  # Changed function call
        filtered_movies = [
            movie for movie in movies[:5]
            if movie.get('release_date') and movie.get('vote_average') is not None and movie.get('poster_path')
        ]
        
        if filtered_movies:
            # Display original results
            st.subheader("Recommendations:")
            # Prepare HTML for tabular display
            table_html = "<table style='width:100%;'><tr>"
            table_html += "<th>Image</th><th>Title</th><th>Release Date</th><th>Vote Average</th><th>Vote Count</th><th>Popularity</th><th>Overview</th></tr>"
            
            for movie in filtered_movies:
                table_html += "<tr>"
                table_html += f"<td><img src='https://image.tmdb.org/t/p/w200{movie['poster_path']}' style='width:150px;'/></td>"  # Increased image size
                table_html += f"<td>{movie['title']}</td>"
                table_html += f"<td>{movie['release_date']}</td>"
                table_html += f"<td>{movie['vote_average']}</td>"
                table_html += f"<td>{movie['vote_count']}</td>"
                table_html += f"<td>{movie['popularity']}</td>"
                table_html += f"<td>{movie['overview'][:100]}...</td>"
                table_html += "</tr>"
            
            table_html += "</table>"
            
            # Display the HTML table
            st.markdown(table_html, unsafe_allow_html=True)

            # Add enhanced recommendations section
            st.subheader("Movies You Might Like:")
            
            # Get genres for the first movie
            first_movie = filtered_movies[0]
            genre_ids = first_movie.get('genre_ids', [])
            
            if genre_ids:
                # Get genre names
                genres = get_genre_list(TMDB_API_KEY)
                genre_names = [genres.get(gid, "Unknown") for gid in genre_ids]
                
                # Display genres of the selected movie
                st.write(f"Based on genres: {', '.join(genre_names)}")
                
                # Get recommendations for each genre combination
                recommendations = get_recommendations_by_genres(genre_ids, TMDB_API_KEY)
                
                if recommendations:
                    # Filter out the original movie from recommendations
                    recommendations = [r for r in recommendations if r['id'] != first_movie['id']][:5]
                    
                    # Create table for recommendations
                    rec_table_html = "<table style='width:100%;'><tr>"
                    rec_table_html += "<th>Image</th><th>Title</th><th>Release Date</th><th>Vote Average</th><th>Genres</th><th>Overview</th></tr>"
                    
                    for rec in recommendations:
                        if rec.get('poster_path') and rec.get('release_date'):
                            # Get genre names for this recommendation
                            rec_genre_ids = rec.get('genre_ids', [])
                            rec_genre_names = [genres.get(gid, "Unknown") for gid in rec_genre_ids]
                            
                            rec_table_html += "<tr>"
                            rec_table_html += f"<td><img src='https://image.tmdb.org/t/p/w200{rec['poster_path']}' style='width:150px;'/></td>"
                            rec_table_html += f"<td>{rec['title']}</td>"
                            rec_table_html += f"<td>{rec['release_date']}</td>"
                            rec_table_html += f"<td>{rec['vote_average']:.1f}</td>"
                            rec_table_html += f"<td>{', '.join(rec_genre_names[:3])}</td>"  # Show first 3 genres
                            rec_table_html += f"<td>{rec['overview'][:100]}...</td>"
                            rec_table_html += "</tr>"
                    
                    rec_table_html += "</table>"
                    st.markdown(rec_table_html, unsafe_allow_html=True)
                else:
                    st.write("No recommendations found.")
        else:
            st.write("No movies found with complete data.")

        # Add international recommendations section
        st.subheader("Explore Movies from Different Industries")
        
        # Create tabs for different industries
        tabs = st.tabs(["Hollywood", "Bollywood", "Korean", "Japanese", "Chinese", "French", "Spanish"])
        
        regions = [None, 'IN', 'KR', 'JP', 'HK', 'FR', 'ES']
        
        for tab, region in zip(tabs, regions):
            with tab:
                recommendations = get_region_recommendations(TMDB_API_KEY, region)
                
                if recommendations:
                    # Create table for regional recommendations
                    reg_table_html = "<table style='width:100%;'><tr>"
                    reg_table_html += "<th>Image</th><th>Title</th><th>Original Title</th><th>Release Date</th><th>Vote Average</th><th>Overview</th></tr>"
                    
                    for rec in recommendations[:5]:  # Show top 5 movies
                        if rec.get('poster_path') and rec.get('release_date'):
                            reg_table_html += "<tr>"
                            reg_table_html += f"<td><img src='https://image.tmdb.org/t/p/w200{rec['poster_path']}' style='width:150px;'/></td>"
                            reg_table_html += f"<td>{rec['title']}</td>"
                            reg_table_html += f"<td>{rec.get('original_title', rec['title'])}</td>"
                            reg_table_html += f"<td>{rec['release_date']}</td>"
                            reg_table_html += f"<td>{rec['vote_average']:.1f}</td>"
                            reg_table_html += f"<td>{rec['overview'][:100]}...</td>"
                            reg_table_html += "</tr>"
                    
                    reg_table_html += "</table>"
                    st.markdown(reg_table_html, unsafe_allow_html=True)
                else:
                    st.write("No recommendations found for this region.")

# Actor Search Tab
with tab_actor:
    st.header("Recommend by Actor/Actress")
    actor_name = st.text_input("Enter actor/actress name:", key="actor_recommend")  # Changed key
    
    # Store the selected actor ID in session state
    if 'selected_actor_id' not in st.session_state:
        st.session_state.selected_actor_id = None
    if 'selected_actor_name' not in st.session_state:
        st.session_state.selected_actor_name = None

    if actor_name:
        persons = recommend_person(actor_name, TMDB_API_KEY)  # Changed function call
        
        if persons:
            person_options = {f"{person['name']} ({person.get('known_for_department', 'Actor')})": person['id'] 
                             for person in persons[:5]}
            
            selected_person_name = st.selectbox(
                "Select the person for recommendations:",  # Updated prompt
                options=list(person_options.keys())
            )
            
            if selected_person_name:
                st.session_state.selected_actor_id = person_options[selected_person_name]
                st.session_state.selected_actor_name = selected_person_name.split('(')[0].strip()

    # Display movies for either searched actor or clicked similar actor
    if st.session_state.selected_actor_id:
        filtered_movies = display_actor_movies(st.session_state.selected_actor_id, 
                                             st.session_state.selected_actor_name, 
                                             TMDB_API_KEY)
        
        if filtered_movies:
            # Add a section for similar actors
            st.subheader("You might also like movies from:")
            similar_actors = set()
            for movie in filtered_movies[:5]:
                credits_url = f"{BASE_URL}/movie/{movie['id']}/credits"
                params = {'api_key': TMDB_API_KEY}
                response = requests.get(credits_url, params=params)
                if response.status_code == 200:
                    cast = response.json().get('cast', [])
                    for actor in cast[:3]:  # Get top 3 actors from each movie
                        if actor['id'] != st.session_state.selected_actor_id:
                            similar_actors.add((actor['name'], actor['id']))
            
            # Display similar actors as buttons
            cols = st.columns(3)
            for idx, (similar_actor_name, similar_actor_id) in enumerate(list(similar_actors)[:6]):
                with cols[idx % 3]:
                    if st.button(similar_actor_name, key=f"similar_actor_{similar_actor_id}"):
                        st.session_state.selected_actor_id = similar_actor_id
                        st.session_state.selected_actor_name = similar_actor_name
                        # Instead of rerunning, just update the session state
                        # The UI will automatically update on the next interaction

# Genre Browse Tab
with tab_genre:
    st.header("Browse by Genre")
    
    # Get list of genres
    genres = get_genre_list(TMDB_API_KEY)
    
    # Create genre selection
    selected_genres = st.multiselect(
        "Select genres:",
        options=list(genres.values()),
        key="genre_select"
    )
    
    if selected_genres:
        # Convert genre names back to IDs
        genre_ids = [
            genre_id for genre_id, genre_name in genres.items()
            if genre_name in selected_genres
        ]
        
        # Get recommendations for selected genres
        recommendations = get_recommendations_by_genres(genre_ids, TMDB_API_KEY)
        
        if recommendations:
            st.subheader(f"Recommended Movies for {', '.join(selected_genres)}")
            
            # Create table for genre recommendations
            genre_table_html = "<table style='width:100%;'><tr>"
            genre_table_html += "<th>Image</th><th>Title</th><th>Release Date</th><th>Vote Average</th><th>Genres</th><th>Overview</th></tr>"
            
            for movie in recommendations[:10]:
                if movie.get('poster_path') and movie.get('release_date'):
                    movie_genre_ids = movie.get('genre_ids', [])
                    movie_genre_names = [genres.get(gid, "Unknown") for gid in movie_genre_ids]
                    
                    genre_table_html += "<tr>"
                    genre_table_html += f"<td><img src='https://image.tmdb.org/t/p/w200{movie['poster_path']}' style='width:150px;'/></td>"
                    genre_table_html += f"<td>{movie['title']}</td>"
                    genre_table_html += f"<td>{movie['release_date']}</td>"
                    genre_table_html += f"<td>{movie.get('vote_average', 'N/A'):.1f}</td>"
                    genre_table_html += f"<td>{', '.join(movie_genre_names[:3])}</td>"
                    genre_table_html += f"<td>{movie.get('overview', '')[:100]}...</td>"
                    genre_table_html += "</tr>"
            
            genre_table_html += "</table>"
            st.markdown(genre_table_html, unsafe_allow_html=True)
            
            # Industry-specific recommendations with the same genres
            st.subheader(f"Explore {', '.join(selected_genres)} Movies from Different Industries")
            
            regions = {
                "Hollywood": {"code": None, "language": "en"},
                "Bollywood": {"code": "IN", "language": "hi"},
                "Korean Cinema": {"code": "KR", "language": "ko"},
                "Japanese Cinema": {"code": "JP", "language": "ja"},
                "Chinese Cinema": {"code": "HK", "language": "zh"},
                "French Cinema": {"code": "FR", "language": "fr"},
                "Spanish Cinema": {"code": "ES", "language": "es"}
            }
            
            def get_industry_recommendations(region_info, genre_ids):
                """Get recommendations for specific industry and genres"""
                params = {
                    'api_key': TMDB_API_KEY,
                    'with_genres': ','.join(map(str, genre_ids)),
                    'sort_by': 'popularity.desc',
                    'vote_count.gte': 100,
                    'page': 1,
                    'language': 'en'  # Keep English as display language
                }
                
                if region_info["code"]:
                    params['region'] = region_info["code"]
                    params['with_original_language'] = region_info["language"]
                
                response = requests.get(DISCOVER_URL, params=params)
                if response.status_code == 200:
                    return response.json().get('results', [])
                return []
            
            # Create columns for industry buttons
            cols = st.columns(3)
            for idx, (region_name, region_info) in enumerate(regions.items()):
                with cols[idx % 3]:
                    if st.button(f"{region_name} {', '.join(selected_genres)} Movies"):
                        industry_recommendations = get_industry_recommendations(region_info, genre_ids)
                        
                        if industry_recommendations:
                            st.subheader(f"{region_name} - {', '.join(selected_genres)} Movies")
                            
                            # Create table for industry-specific recommendations
                            ind_table_html = "<table style='width:100%;'><tr>"
                            ind_table_html += "<th>Image</th><th>Title</th><th>Original Title</th><th>Release Date</th><th>Vote Average</th><th>Overview</th></tr>"
                            
                            for rec in industry_recommendations[:5]:
                                if rec.get('poster_path') and rec.get('release_date'):
                                    ind_table_html += "<tr>"
                                    ind_table_html += f"<td><img src='https://image.tmdb.org/t/p/w200{rec['poster_path']}' style='width:150px;'/></td>"
                                    ind_table_html += f"<td>{rec['title']}</td>"
                                    ind_table_html += f"<td>{rec.get('original_title', rec['title'])}</td>"
                                    ind_table_html += f"<td>{rec['release_date']}</td>"
                                    ind_table_html += f"<td>{rec['vote_average']:.1f}</td>"
                                    ind_table_html += f"<td>{rec['overview'][:100]}...</td>"
                                    ind_table_html += "</tr>"
                            
                            ind_table_html += "</table>"
                            st.markdown(ind_table_html, unsafe_allow_html=True)
                        else:
                            st.write(f"No {', '.join(selected_genres)} movies found in {region_name}.")
