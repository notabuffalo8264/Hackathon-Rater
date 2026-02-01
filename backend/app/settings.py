from pydantic import BaseModel


class Settings(BaseModel):
    # Base dir
    data_dir: str = "data"

    # Dual FAISS indexes
    index_all_path: str = "data/index_all.faiss"
    index_recent_path: str = "data/index_recent.faiss"
    recent_row_ids_path: str = "data/recent_row_ids.json"

    # Metadata aligned to index rows
    meta_path: str = "data/projects_meta.json"

    # Embedding model
    embed_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"

    # API defaults
    top_k_default: int = 5
    recent_months: int = 24


settings = Settings()