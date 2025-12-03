#!/usr/bin/env python3
"""
Script to create and populate the gubernamental documents corpus with predefined documents.
This script should be run once to set up the RAG corpus before using the agent.
"""

import os
import sys
import argparse
from typing import List

import vertexai
from vertexai import rag
from dotenv import load_dotenv

from config import (
    PROJECT_ID,
    LOCATION,
    CORPUS_NAME,
    CORPUS_DISPLAY_NAME,
    DEFAULT_EMBEDDING_MODEL,
    DEFAULT_CHUNK_SIZE,
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_EMBEDDING_REQUESTS_PER_MIN,
)


def initialize_vertex_ai():
    """Initialize Vertex AI with project configuration."""
    try:
        if not PROJECT_ID or not LOCATION:
            raise ValueError(
                "Missing required environment variables. "
                "Please set GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION"
            )
        
        print(f"Initializing Vertex AI with project={PROJECT_ID}, location={LOCATION}")
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        print("✅ Vertex AI initialization successful")
        
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI: {str(e)}")
        print("Please check your Google Cloud credentials and project settings.")
        sys.exit(1)


def check_corpus_exists() -> bool:
    """Check if the corpus already exists."""
    try:
        corpus_resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_NAME}"
        corpora = rag.list_corpora()
        
        for corpus in corpora:
            if corpus.name == corpus_resource_name:
                print(f"✅ Corpus '{CORPUS_DISPLAY_NAME}' already exists")
                return True
                
        return False
        
    except Exception as e:
        print(f"❌ Error checking corpus existence: {str(e)}")
        return False


def create_corpus() -> str:
    """Create a new RAG corpus for governmental documents."""
    try:
        print(f"🚀 Creating corpus: {CORPUS_DISPLAY_NAME}")
        
        # Configure embedding model
        embedding_model_config = rag.RagEmbeddingModelConfig(
            vertex_prediction_endpoint=rag.VertexPredictionEndpoint(
                publisher_model=DEFAULT_EMBEDDING_MODEL
            )
        )

        # Create the corpus
        rag_corpus = rag.create_corpus(
            display_name=CORPUS_DISPLAY_NAME,
            backend_config=rag.RagVectorDbConfig(
                rag_embedding_model_config=embedding_model_config
            ),
        )
        
        print(f"✅ Successfully created corpus: {rag_corpus.name}")
        return rag_corpus.name
        
    except Exception as e:
        print(f"❌ Error creating corpus: {str(e)}")
        sys.exit(1)


def add_documents_to_corpus(corpus_resource_name: str, document_paths: List[str]):
    """Add documents to the corpus."""
    try:
        if not document_paths:
            print("⚠️  No document paths provided")
            return
            
        print(f"📄 Adding {len(document_paths)} documents to corpus...")
        
        # Validate document paths
        validated_paths = []
        for path in document_paths:
            if path.startswith("gs://") or path.startswith("https://drive.google.com/"):
                validated_paths.append(path)
                print(f"  ✓ {path}")
            else:
                print(f"  ❌ Invalid path format: {path}")
                
        if not validated_paths:
            print("❌ No valid document paths found")
            return
            
        # Set up chunking configuration
        transformation_config = rag.TransformationConfig(
            chunking_config=rag.ChunkingConfig(
                chunk_size=DEFAULT_CHUNK_SIZE,
                chunk_overlap=DEFAULT_CHUNK_OVERLAP,
            ),
        )

        # Import files to the corpus
        import_result = rag.import_files(
            corpus_resource_name,
            validated_paths,
            transformation_config=transformation_config,
            max_embedding_requests_per_min=DEFAULT_EMBEDDING_REQUESTS_PER_MIN,
        )

        print(f"✅ Successfully added {import_result.imported_rag_files_count} files to corpus")
        
    except Exception as e:
        print(f"❌ Error adding documents to corpus: {str(e)}")


def get_default_document_paths() -> List[str]:
    """
    Get default document paths for governmental documents.
    
    These should be replaced with actual Google Drive URLs or GCS paths
    containing your governmental documents.
    """
    # Example paths - replace these with your actual document URLs
    return [
        # Google Drive URLs (example format)
        # "https://drive.google.com/file/d/YOUR_FILE_ID_1/view",
        # "https://drive.google.com/file/d/YOUR_FILE_ID_2/view",
        
        # Google Cloud Storage paths (example format)  
        # "gs://your-bucket/governmental-docs/regulations.pdf",
        # "gs://your-bucket/governmental-docs/procedures.pdf",
        
        # Add your actual document paths here
    ]


def main():
    """Main function to set up the governmental documents corpus."""
    parser = argparse.ArgumentParser(
        description="Setup governmental documents RAG corpus"
    )
    parser.add_argument(
        "--documents", 
        nargs="+", 
        help="List of document paths (Google Drive URLs or GCS paths)",
        default=None
    )
    parser.add_argument(
        "--force",
        action="store_true", 
        help="Force recreation of corpus if it already exists"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Initialize Vertex AI
    initialize_vertex_ai()
    
    # Check if corpus exists
    corpus_exists = check_corpus_exists()
    
    if corpus_exists and not args.force:
        print("ℹ️  Corpus already exists. Use --force to recreate it.")
        
        # Still allow adding more documents
        if args.documents:
            corpus_resource_name = f"projects/{PROJECT_ID}/locations/{LOCATION}/ragCorpora/{CORPUS_NAME}"
            add_documents_to_corpus(corpus_resource_name, args.documents)
        return
    
    # Create corpus (or recreate if forced)
    corpus_resource_name = create_corpus()
    
    # Get document paths
    document_paths = args.documents or get_default_document_paths()
    
    if not document_paths:
        print("\n⚠️  No document paths provided!")
        print("Please provide document paths using --documents argument")
        print("Example:")
        print("  python setup_corpus.py --documents \\")
        print('    "https://drive.google.com/file/d/YOUR_FILE_ID/view" \\')
        print('    "gs://your-bucket/docs/regulations.pdf"')
        print("\nOr edit get_default_document_paths() function to add default paths.")
        return
    
    # Add documents to corpus
    add_documents_to_corpus(corpus_resource_name, document_paths)
    
    print("\n🎉 Corpus setup complete!")
    print(f"Corpus name: {CORPUS_DISPLAY_NAME}")
    print(f"Resource name: {corpus_resource_name}")
    print("You can now use the RAG agent to query the governmental documents.")


if __name__ == "__main__":
    main()