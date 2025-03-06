# Dockerfile
FROM python:3.11-slim-bullseye

WORKDIR /st_custom_portal_app

COPY requirements.txt /st_custom_portal_app/

RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . /st_custom_portal_app/

EXPOSE 8501

CMD ["streamlit","run", "app.py"]