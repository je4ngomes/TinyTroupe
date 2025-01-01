# # Use Python 3.10.16 as recommended
# FROM python:3.10.16-slim

# # 1) Install system dependencies (git, etc. if needed)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     git \
#     && rm -rf /var/lib/apt/lists/*

# # 2) Set the working directory
# WORKDIR /app

# # 3) Copy everything from your local `~/tinytroupe` project into /app
# #    (You might use a .dockerignore to exclude big/unnecessary folders.)
# COPY . /app

# # 4) Install the project in editable mode (-e .) from /app
# #    This should find the pyproject.toml or setup.py in /app.
# RUN pip install --no-cache-dir -e .

# # 5) Expose FastAPI’s default port (if needed)
# EXPOSE 8000

# # 6) Start your desired API, for instance story_api
# CMD ["uvicorn", "story_api:app", "--host", "0.0.0.0", "--port", "8000"]
# Dockerfile (~/tinytroupe/Dockerfile)

FROM python:3.10.16-slim

# 1) Install system dependencies (git, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2) Set working directory
WORKDIR /app

# 3) Copy everything from your local 'tinytroupe' project into /app
COPY . /app

# 4) Install the entire project in editable mode
#    This picks up the pyproject.toml/setup.py in /app
RUN pip install --no-cache-dir -e .
RUN pip install FastAPI
RUN pip install uvicorn

# 5) Expose port (if running a FastAPI)
EXPOSE 8000

# 6) Default command: run story_api
CMD ["uvicorn", "tinytroupe.story_api:app", "--host", "0.0.0.0", "--port", "8000"]
