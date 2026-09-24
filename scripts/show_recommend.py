import pandas as pd
import sqlite3
import pickle
import streamlit as st
import logging

logging.basicConfig(
    filename="Logs/recommend.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s — %(levelname)s — %(message)s",
    force=True
)

conn = sqlite3.connect(r"Data\shows.db")

shows = pd.read_sql_query("SELECT * FROM Dataset", conn)
similarity = pickle.load(open(r"Data\similarity.pkl", "rb"))

# Utilities
def recommend(show_name: str, n:int = 5) -> list:
    """It takes show name as input and recommend 5 similar shows."""
    try:
        if not isinstance(show_name, str):
            raise TypeError("Show name must be string")
        
        show_idx = shows[shows["title"] == show_name].index[0]
        dist = similarity[show_idx]
        show_list = sorted(list(enumerate(dist)), reverse=True, key=lambda x: x[1])[1:n+1]

        rec_shows = []
        for i in show_list:
            title = shows["title"].iloc[i[0]]
            rec_shows.append(title)
        return rec_shows
    except Exception as e:
        logging.error(f"Failed to recommend shows: {e}", exc_info=True)

st.markdown("""
<div class="hero">
    <h1>NETFLIX</h1>
    <h2>Show Recommendation System</h2>
    <p>Discover your next binge-worthy series.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### 🎬 Find similar shows")

select_movie_name = st.selectbox(
    "Choose a show",
    shows["title"].values,
    label_visibility="collapsed"
)

if st.button("RECOMMEND"):
    recommendations = recommend(select_movie_name)
    st.markdown("""
    <style>
    .rec-card {
        padding: 18px;
        border-radius: 14px;
        background: #181818;
        border: 1px solid #303030;
        margin-bottom: 12px;
        transition: 0.2s;
    }

    .rec-card:hover {
        border-color: #e50914;
        transform: translateY(-2px);
    }

    .rec-title {
        font-size: 18px;
        font-weight: 600;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    for show in recommendations:
        st.markdown(
            f"""
            <div class="rec-card">
                <div class="rec-title">{show}</div>
            </div>
            """,
            unsafe_allow_html=True
        )