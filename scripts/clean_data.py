import pandas as pd
import sqlite3
import time
import logging
import sys
from pathlib import Path
import pickle
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from load_data import ingest_data

logging.basicConfig(
    filename="Logs/clean_data.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True
)

def ensure_wordnet():
    """Ensure WordNet is available inside the active virtual environment."""

    nltk_data_dir = Path(sys.prefix) / "nltk_data"
    nltk_data_dir.mkdir(parents=True, exist_ok=True)

    # Tell NLTK to search this environment-specific directory first.
    if str(nltk_data_dir) not in nltk.data.path:
        nltk.data.path.insert(0, str(nltk_data_dir))

    try:
        wordnet.synsets("running")
        logging.info("WordNet corpus is already available.")
        return

    except LookupError:
        logging.info(
            "WordNet corpus not found. Downloading to %s",
            nltk_data_dir
        )

    success = nltk.download(
        "wordnet",
        download_dir=str(nltk_data_dir),
        quiet=True
    )

    if not success:
        raise RuntimeError("Failed to download NLTK WordNet corpus.")

    try:
        wordnet.synsets("running")
    except LookupError as e:
        raise RuntimeError(
            f"WordNet is still unavailable. "
            f"NLTK data paths: {nltk.data.path}"
        ) from e

    logging.info("WordNet corpus downloaded and verified.")

ensure_wordnet()

# Check existance of database on given path
def database_exists(db_path: str) -> bool:
    """Returns True if Sqlite database file exists at given path."""
    path = Path(db_path)
    return path.is_file() and path.suffix.lower() == ".db"

# Convert word to its root form
def lemma(text):
    result = [WordNetLemmatizer().lemmatize(w) for w in text]
    return " ".join(result)

# Cleaning Dataframe
def clean_df(df_b: pd.DataFrame) -> pd.DataFrame:
    """Cleans i.e removing leading or trailing spaces, converting to lower case,
      creates tags by concating type, rating, description, listed_in columns"""
    try:
        start = time.time()

        if not isinstance(df_b, pd.DataFrame):
            raise TypeError("Dataframe must be pandas dataframe")
        
        logging.info("Started data cleaning. shape = %s", df_b.shape)

        req_columns = ["show_id", "type", "title", "director", "rating", "listed_in"]
        if "description" in df_b.columns:
            req_columns.append("description")
        
        df = df_b[req_columns].dropna().copy()
        
        for i in ["type", "rating"]:
            df[i] = df[i].str.lower().str.strip().str.replace(r"[^\w]", "", regex=True).str.split()

        df["director"] = df["director"].str.lower().str.strip().str.replace(" ", "").str.replace(",", " ").str.replace(r"[^\w\s]", "", regex=True).str.split()
        df["listed_in"] = df["listed_in"].str.lower().str.replace(r"\s+\b(tv|shows|movies)\b|[^\w\s]", "", regex=True).str.strip().str.split()

        tag_cols = ["listed_in", "director", "type", "rating"]

        if "description" in df.columns:
            df["description"] = df["description"].str.lower().str.replace("-", " ").str.replace(r"[^\w\s]", "", regex=True).str.split()
            tag_cols.insert(0, "description")

        df["tags"] = df[tag_cols].sum(axis=1).apply(lemma)
        df = df[["show_id", "title", "tags"]]

        end = time.time()
        total_time = (end-start)/60

        logging.info("Succesfully cleaned data. new dataframe shape = %s", df.shape)
        logging.info(f"\nTotal time taken {total_time} minutes")

        return df

    except Exception as e:
        logging.error(f"Failed to clean dataframe: {e}", exc_info=True)
        raise


def create_similarity_vectors(df: pd.DataFrame, col: str):
    """Create similarity vectors by using TF-IDF as vectorizer
        and cosine similarity to find similarity score between those vectors
        also saves it into similarity array"""
    try:
        start = time.time()

        if not isinstance(df, pd.DataFrame):
            raise TypeError("Dataframe Must be pandas dataframe")
        if col not in df.columns:
            raise KeyError(f"Required Column {col} is missing from dataframe")
        
        logging.info("Started Creating similarity Vectors")
        vectors = TfidfVectorizer(stop_words="english", max_features=5000).fit_transform(df[col]).toarray()
        similarity = cosine_similarity(vectors)

        end = time.time()
        tt = (end-start)/60
        logging.info("Successfully created similarity vectors")
        logging.info(f"\nTotal time taken {tt} minutes")
        return similarity
    except Exception as e:
        logging.error("Failed to create similarity Vectors: {e}", exc_info=True)
        raise

if __name__ == "__main__":

    database_path = r"Data\shows.db"
    try:
        if database_exists(database_path):
            conn = sqlite3.connect(database_path)
            data = pd.read_sql_query("SELECT * FROM Dataset", conn)
            new_df = clean_df(data)

            if isinstance(new_df, pd.DataFrame):
                logging.info(f"\n{new_df.head()}")
                ingest_data(new_df, "recommendation_df", conn)

                similarity = create_similarity_vectors(new_df, "tags")
                pickle.dump(similarity, open("Data/similarity.pkl", "wb"))
            else:
                TypeError("Dataframe Must be pandas dataframe")

        else:
            raise FileNotFoundError(f"Database is not present at given path: {database_path}")
    except Exception as e:
        logging.error(f"Failed to find database on given path: {e}", exc_info=True)