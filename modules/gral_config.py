import os

page_config = {"page_title":"CustomsPortal", 
               "page_icon":":customs:", 
               "layout":"wide", 
               "initial_sidebar_state":"auto"}

back_url_config = {
    "risk_url": os.environ.get("RISK_URL", "http://localhost:5000"),
    "rag_url": os.environ.get("RAG_URL", "http://localhost:8080"),
    "clasi_url": os.environ.get("CLASI_URL", "http://localhost:8000")
}