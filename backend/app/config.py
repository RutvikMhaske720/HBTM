from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "./data"
    database_url: str = "sqlite:///./data/iabtm.db"
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
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "iabtm-curator/0.1"
    web_search_provider: str = ""
    web_search_api_key: str = ""
    openai_api_key: str = ""

    frontend_origin: str = "http://localhost:3000"

    @property
    def youtube_mocked(self) -> bool:
        return not self.youtube_api_key

    @property
    def pinterest_configured(self) -> bool:
        return bool(self.pinterest_board_id and (self.pinterest_access_token or (
            self.pinterest_client_id and self.pinterest_client_secret
        )))

    @property
    def spotify_configured(self) -> bool:
        return bool(self.spotify_client_id and self.spotify_client_secret)


    @property
    def reddit_mocked(self) -> bool:
        return not (self.reddit_client_id and self.reddit_client_secret)

    @property
    def web_search_mocked(self) -> bool:
        return not self.web_search_api_key

    @property
    def embeddings_mocked(self) -> bool:
        # True local embeddings (TF-IDF) rather than OpenAI — "mocked" here
        # just means "not the real embedding model from the spec."
        return not self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
