from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    data_dir: str = "./data"

    youtube_api_key: str = ""
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
