#!/usr/bin/env python3
"""
Test script for the Gubernamental RAG Agent.
"""

import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_agent.agent import root_agent
from rag_agent.tools.utils import check_corpus_exists


def test_corpus_existence():
    """Test if the corpus exists."""
    print("🔍 Checking if corpus exists...")
    
    try:
        exists = check_corpus_exists()
        if exists:
            print("✅ Corpus exists and is accessible")
            return True
        else:
            print("❌ Corpus not found. Please run setup_corpus.py first")
            return False
            
    except Exception as e:
        print(f"❌ Error checking corpus: {str(e)}")
        return False


def test_agent_initialization():
    """Test if the agent initializes correctly."""
    print("\n🤖 Testing agent initialization...")
    
    try:
        agent = root_agent
        print(f"✅ Agent initialized: {agent.name}")
        print(f"   Model: {agent.model}")
        print(f"   Tools: {[tool.__name__ for tool in agent.tools]}")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing agent: {str(e)}")
        return False


def test_simple_query():
    """Test a simple RAG query."""
    print("\n🔎 Testing simple RAG query...")
    
    try:
        from google.adk.tools.tool_context import ToolContext
        from rag_agent.tools.rag_query import rag_query
        
        # Create a test context
        tool_context = ToolContext()
        tool_context.state = {}
        
        # Test query
        test_query = "¿Cuáles son los requisitos para un trámite?"
        
        result = rag_query(test_query, tool_context)
        
        print(f"Query: {test_query}")
        print(f"Status: {result.get('status')}")
        print(f"Message: {result.get('message')}")
        
        if result.get('status') == 'success':
            print(f"Results found: {result.get('results_count', 0)}")
            print("✅ RAG query successful")
            return True
        elif result.get('status') == 'warning':
            print("⚠️  Query executed but no results found")
            return True
        else:
            print("❌ RAG query failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing RAG query: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("🧪 Testing Gubernamental RAG Agent\n")
    
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("❌ GOOGLE_CLOUD_PROJECT environment variable not set")
        return
        
    if not os.environ.get("GOOGLE_CLOUD_LOCATION"):
        print("❌ GOOGLE_CLOUD_LOCATION environment variable not set") 
        return
    
    print(f"Project: {os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    print(f"Location: {os.environ.get('GOOGLE_CLOUD_LOCATION')}")
    
    # Run tests
    tests = [
        test_corpus_existence,
        test_agent_initialization,
        test_simple_query,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {str(e)}")
            results.append(False)
    
    # Summary
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! RAG agent is ready to use.")
    else:
        print("⚠️  Some tests failed. Please check the setup.")
        
        if not results[0]:  # Corpus doesn't exist
            print("\n💡 To fix corpus issues, run:")
            print("   python rag_agent/setup_corpus.py --documents YOUR_DOCUMENT_URLS")


if __name__ == "__main__":
    main()