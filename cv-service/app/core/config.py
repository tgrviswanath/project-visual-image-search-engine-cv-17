from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SERVICE_NAME: str = "Visual Image Search Engine CV Service"
    SERVICE_VERSION: str = "1.0.0"
    SERVICE_PORT: int = 8001
    MAX_IMAGE_SIZE: int = 224
    TOP_K: int = 5

    class Config:
        env_file = ".env"

settings = Settings()
