import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# TMDB API configuration
TMDB_API_KEY = os.environ.get('TMDB_API_KEY'
                              )
if not TMDB_API_KEY:
    st.error("TMDB API key not found. Please set the TMDB_API_KEY environment variable.")
    st.stop()

BASE_URL = "https://api.themoviedb.org/3"
SEARCH_URL = f"{BASE_URL}/search/movie"

def search_movie(query):
    params = {
        'api_key': TMDB_API_KEY,
        'query': query
    }
    response = requests.get(SEARCH_URL, params=params)
    if response.status_code == 200:
        return response.json()['results']
    else:
        st.error(f"Error fetching data: {response.status_code}")
        return []

st.title("Movie Recommendation System")
st.markdown("**Created by Harsh Bajpay**")

movie_name = st.text_input("Enter a movie name:")

if movie_name:
    movies = search_movie(movie_name)
    # Filter out movies with missing data
    filtered_movies = [
        movie for movie in movies[:5]
        if movie.get('release_date') and movie.get('vote_average') is not None and movie.get('poster_path')
    ]
    
    if filtered_movies:
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
    else:
        st.write("No movies found with complete data.")
