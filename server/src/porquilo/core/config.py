from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_engine: str = "sqlite"
    
    # SQLite
    sqlite_path: str = "/data/porquilo.db"
    
    # Postgres
    postgres_user: str = "porquilo"
    postgres_password: str = ""
    postgres_server: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "porquilo"

    @property
    def database_url(self) -> str:
        if self.db_engine == "postgres":
            return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"
        return f"sqlite:///{self.sqlite_path}"

settings = Settings()