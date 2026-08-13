FROM python:3.14-slim

WORKDIR /app/api

# Install poetry
RUN pip install poetry

# Store venv OUTSIDE project dir — avoids being hidden by the ./api volume mount
RUN poetry config virtualenvs.in-project true

