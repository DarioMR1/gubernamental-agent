import os
from datetime import datetime
from typing import List, Dict, Optional

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sentence_transformers import SentenceTransformer
import faiss
import pickle

load_dotenv()
EMBED_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
FAISS_INDEX_PATH = "./faiss_store/index.faiss"
FAISS_META_PATH = "./faiss_store/meta.pkl"
index = None
metadata_store = []  # parallel array to store metadata for each vector

GOOGLE_FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID")

def load_faiss_index():
    global index, metadata_store

    if os.path.exists(FAISS_INDEX_PATH):
        index = faiss.read_index(FAISS_INDEX_PATH)

        with open(FAISS_META_PATH, "rb") as f:
            metadata_store = pickle.load(f)
    else:
        index = faiss.IndexFlatL2(384)  # MiniLM dimension = 384
        metadata_store = []

def save_faiss_index():
    faiss.write_index(index, FAISS_INDEX_PATH)
    with open(FAISS_META_PATH, "wb") as f:
        pickle.dump(metadata_store, f)


# GOOGLE DRIVE FETCHER

def fetch_drive_documents() -> List[Dict]:
    """
    Returns a list of {id, name, text} for each file in the folder.
    Converts Google Docs → plain text automatically.
    We will only be using case 1
    """

    creds = Credentials(
        token=os.getenv("GOOGLE_ACCESS_TOKEN"),
        refresh_token=os.getenv("GOOGLE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET")
    )

    service = build("drive", "v3", credentials=creds)

    # List files in folder
    results = service.files().list(
        q=f"'{GOOGLE_FOLDER_ID}' in parents",
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])
    output = []

    for f in files:
        file_id = f["id"]
        mime = f["mimeType"]

        # Case 1: Google Docs → export to text/plain
        if mime == "application/vnd.google-apps.document":
            text = service.files().export(fileId=file_id, mimeType="text/plain").execute().decode("utf-8")

        # Case 2: PDFs → skip or OCR (optional)
        elif mime == "application/pdf":
            continue  # keeping simple for now

        # Case 3: .txt
        else:
            content = service.files().get_media(fileId=file_id).execute()
            text = content.decode("utf-8", errors="ignore")

        output.append({
            "id": file_id,
            "name": f["name"],
            "text": text
        })

    return output



def index_drive_documents(tool_context: ToolContext) -> dict:
    """
    Encode docs → add to FAISS index → save index.
    """
    global metadata_store

    load_faiss_index()
    docs = fetch_drive_documents()

    for d in docs:
        emb = EMBED_MODEL.encode([d["text"]])[0].astype("float32")
        index.add(emb.reshape(1, -1))

        metadata_store.append({
            "id": d["id"],
            "name": d["name"],
            "text": d["text"]
        })

    save_faiss_index()

    return {
        "status": "success",
        "indexed_documents": len(docs)
    }


def query_drive_rag(tool_context: ToolContext, query: str, k: int = 4) -> dict:
    """
    Embed query → FAISS search → returns top documents.
    """
    print("🔥 [RAG] Query received →", query)

    load_faiss_index()

    if index.ntotal == 0:
        return {
            "status": "error",
            "context": "No FAISS index found or it is empty."
        }

    q_emb = EMBED_MODEL.encode([query])[0].astype("float32")

    distances, indices = index.search(q_emb.reshape(1, -1), k)
    indices = indices[0]

    retrieved_docs = []
    for i in indices:
        if i < len(metadata_store):
            m = metadata_store[i]
            retrieved_docs.append(f"--- {m['name']} ---\n{m['text'][:2000]}")

    context = "\n\n".join(retrieved_docs)

    return {
        "status": "success",
        "context": context
    }


rag_agent = Agent(
    name="rag_agent",
    model="gemini-2.0-flash",
    description="Agent that performs RAG over Google Drive documents.",
    instruction=f"""
Eres un agente de RAG que responde basado EXCLUSIVAMENTE en documentos 
indexados desde Google Drive.

Fecha actual: {datetime.now().strftime("%d %B %Y")}

Si no encuentras la respuesta en los documentos, responde:
"No encontré esta información en los documentos disponibles."

### Cómo debes responder:
- Usa la información recuperada del RAG en `query_drive_rag`.
- Si el contexto es ambiguo, declara que es ambiguo.
- No inventes información.
""",
    tools=[
        index_drive_documents,
        query_drive_rag
    ],
    sub_agents=[]
)



