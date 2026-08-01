from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/iabtm.db"
    database_fallback_to_sqlite: bool = True
    supabase_url: str = ""
    supabase_database_url: str = ""
    supabase_secret_key: str = ""

    youtube_api_key: str = ""
    pinterest_client_id: str = ""
    pinterest_client_secret: str = ""
    pinterest_access_token: str = ""
    pinterest_board_id: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    spotify_market: str = "IN"
    web_search_provider: str = ""
    web_search_api_key: str = ""
    openai_api_key: str = ""

    # --- Curation policy ---------------------------------------------------
    # Nothing reaches a user unless it clears all four gates below: it must be
    # recent, semantically close to the profile, not a near-duplicate of
    # something already curated, and backed by a link + preview that resolve.
    curation_max_age_days: int = 540
    curation_relevance_threshold: float = 0.15
    curation_duplicate_threshold: float = 0.78
    curation_http_timeout: float = 10.0
    curation_max_workers: int = 8
    curation_verify_links: bool = True
    curation_target_per_type: int = 12

    frontend_origin: str = "http://localhost:3000"

    @property
    def youtube_configured(self) -> bool:
        return bool(self.youtube_api_key)

    @property
    def pinterest_configured(self) -> bool:
        return bool(self.pinterest_board_id and (self.pinterest_access_token or (
            self.pinterest_client_id and self.pinterest_client_secret
        )))

    @property
    def spotify_configured(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)


    @property
    def web_search_configured(self) -> bool:
        """A paid search API is optional — keyless scraping covers the same ground."""
        return bool(self.web_search_api_key and self.web_search_provider)

    @property
    def embeddings_mocked(self) -> bool:
        # True local embeddings (TF-IDF) rather than OpenAI — "mocked" here
        # just means "not the real embedding model from the spec."
        return not self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
