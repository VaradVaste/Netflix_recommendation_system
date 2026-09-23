import pandas as pd
from sqlalchemy import create_engine
import os
import time
import logging

os.makedirs("Data", exist_ok=True)
os.makedirs("Logs", exist_ok=True)


logging.basicConfig(
    filename="Logs/data_load.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s — %(levelname)s — %(message)s"
)

engine = create_engine("sqlite:///Data/shows.db")

def ingest_data(df, table_name, engine):
    """This function ingest the dataframe in database"""
    try:
        df.to_sql(table_name, con=engine, if_exists="replace", index=False)
        logging.info(f"Successfully ingested {table_name} in database")
    except Exception as e:
        logging.error(f"Failed to ingest table {table_name} in database : {e}", exc_info=True)
        raise

def load_raw_data(data_path):
    """Reads the csv fiie from given path and loads it into database"""
    start = time.time()
    for table in os.listdir(data_path):
        if table.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(data_path, table))
                logging.info(f"Ingesting {table} into database")
                ingest_data(df, table[:-4], engine)
            except Exception as e:
                logging.error(f"Failed processing {table}: {e}", exc_info=True)

    end = time.time()
    total_time = (end - start)/60
    logging.info("========== Ingestion Completed ==========")
    logging.info(f"\nTotal Time taken {total_time} minutes")


if __name__ == "__main__":
    load_raw_data("Data")