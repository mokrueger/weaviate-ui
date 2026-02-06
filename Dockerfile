# ---- Install node ----
FROM node:18 as frontend
WORKDIR /app
COPY ./frontend/package.json ./frontend/yarn.lock ./
RUN yarn install --frozen-lockfile
COPY ./frontend .
RUN yarn build

# ---- Install poetry ----
FROM python:3.11-slim as build

ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN pip install poetry
RUN poetry install --no-interaction --no-ansi
COPY --from=frontend /app/dist /app/static
COPY . .

CMD ["uvicorn", "weaviate_ui.main:app", "--host", "0.0.0.0", "--port", "7777"]
