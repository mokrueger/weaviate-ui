import os

import weaviate
from dotenv import load_dotenv
from fastapi import FastAPI
from loguru import logger
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

load_dotenv()

class Settings(BaseSettings):
    """Configuration loaded from environment variables prefixed with `WEAVIATE_`.

    Examples:
      WEAVIATE_HOST=localhost
      WEAVIATE_PORT=8080
      WEAVIATE_SECURE=false
      WEAVIATE_GRPC_HOST=localhost
      WEAVIATE_GRPC_PORT=50051
      WEAVIATE_GRPC_SECURE=false
      WEAVIATE_API_KEY=...
      WEAVIATE_BEARER_TOKEN=...
    """
    # Minimal required
    host: str
    port: int
    grpc_port: int

    # Extra
    grpc_host: str | None = None
    secure: bool = False
    grpc_secure: bool = False

    # Authentication
    api_key: str | None = None
    bearer_token: str | None = None

    model_config = SettingsConfigDict(
        env_prefix="WEAVIATE_",
        env_file=".env",
        extra="ignore",
    )


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings = Settings()

auth_credentials = None

if settings.api_key:
    auth_credentials = weaviate.auth.Auth.api_key(settings.api_key)
elif settings.bearer_token:
    auth_credentials = weaviate.auth.Auth.bearer_token(settings.bearer_token)

grpc_host = settings.grpc_host or settings.host

client = weaviate.connect_to_custom(
    http_host=settings.host,
    http_port=settings.port,
    http_secure=settings.secure,
    grpc_host=grpc_host,
    grpc_port=settings.grpc_port,
    grpc_secure=settings.grpc_secure,
    auth_credentials=auth_credentials,
)


@app.get("/schema")
def schema():
    return client.collections.list_all()


@app.post("/class/{class_name}")
def class0(
    class_name: str,
    offset: int = 0,
    limit: int = 20,
    keyword: str = "",
    certainty: float = 0.65,
    properties: list[str] | None = None,
):
    logger.info(f"{keyword=}, {certainty=}")

    collection = client.collections.get(class_name)
    paginate = {"limit": limit, "offset": offset}

    if keyword:
        query = {"query": keyword, "certainty": certainty}
        metadata = {"return_metadata": ["certainty", "distance"]}
        response = collection.query.near_text(**query, **metadata, **paginate)
        count_response = collection.aggregate.near_text(total_count=True, **query)
    else:
        response = collection.query.fetch_objects(**paginate)
        count_response = collection.aggregate.over_all(total_count=True)

    return {"data": response.objects, "count": count_response.total_count}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
