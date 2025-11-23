"""
Simple test script to verify your LLM setup is working.

Run this to check:
1. API keys are set correctly
2. Packages are installed
3. LLM scorer can make API calls

Usage:
    python test_llm_setup.py
"""

import os
import sys

def test_imports():
    """Test if required packages are installed."""
    print("Testing imports...")
    
    try:
        import openai
        print("✓ OpenAI package installed")
        return "openai"
    except ImportError:
        pass
    
    try:
        import anthropic
        print("✓ Anthropic package installed")
        return "anthropic"
    except ImportError:
        pass
    
    print("✗ No LLM packages found!")
    print("  Install with: pip install openai")
    print("  Or: pip install anthropic")
    return None

def test_api_keys():
    """Test if API keys are set."""
    print("\nTesting API keys...")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_key:
        print(f"✓ OPENAI_API_KEY is set (starts with: {openai_key[:10]}...)")
        return "openai", openai_key
    elif anthropic_key:
        print(f"✓ ANTHROPIC_API_KEY is set (starts with: {anthropic_key[:10]}...)")
        return "anthropic", anthropic_key
    else:
        print("✗ No API keys found in environment variables!")
        print("\nTo set API keys:")
        print("  Windows PowerShell: $env:OPENAI_API_KEY='your-key'")
        print("  Windows CMD: set OPENAI_API_KEY=your-key")
        print("  Mac/Linux: export OPENAI_API_KEY='your-key'")
        return None, None

def test_llm_scorer(provider, api_key):
    """Test if LLM scorer can make API calls."""
    print(f"\nTesting LLM scorer ({provider})...")
    
    try:
        from relevance_scoring import LLMScorer
        
        # Use a small, fast model for testing
        if provider == "openai":
            model = "gpt-4o-mini"
        else:
            model = "claude-3-haiku-20240307"
        
        print(f"  Initializing scorer (model: {model})...")
        llm_scorer = LLMScorer(
            provider=provider,
            model=model,
            api_key=api_key,
            use_explanations=False  # Faster for testing
        )
        print("  ✓ LLM scorer initialized")
        
        # Test with a simple comparison
        print("  Testing API call (this may take 10-20 seconds)...")
        from paper_retrieval.research_paper import ResearchPaper
        
        # Create mock papers for testing
        paper1 = ResearchPaper(
            id="test1",
            url="",
            title="Machine Learning for Image Classification",
            authors=[{"name": "John Doe"}],
            abstract="This paper presents a deep learning approach for image classification using convolutional neural networks.",
            year=2020,
            citation_count=100
        )
        
        paper2 = ResearchPaper(
            id="test2",
            url="",
            title="Convolutional Neural Networks: A Survey",
            authors=[{"name": "Jane Smith"}],
            abstract="A comprehensive survey of convolutional neural network architectures and their applications.",
            year=2021,
            citation_count=200
        )
        
        result = llm_scorer.compute_score(paper1, paper2)
        score = result.get("relevance_score", 0)
        
        print(f"  ✓ API call successful!")
        print(f"  ✓ Test score: {score:.2f} (expected: 0.5-0.9 for similar papers)")
        
        if 0.0 <= score <= 1.0:
            print("\n🎉 Everything is working! You're ready to use LLM scoring.")
            return True
        else:
            print(f"\n⚠️  Warning: Score out of expected range: {score}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your API key is correct")
        print("  2. Check you have credits/balance in your account")
        print("  3. Check your internet connection")
        print("  4. Check API service status (https://status.openai.com/)")
        return False

def main():
    print("="*60)
    print("LLM Setup Test")
    print("="*60)
    
    # Test imports
    provider_pkg = test_imports()
    if not provider_pkg:
        print("\n❌ Please install required packages first.")
        sys.exit(1)
    
    # Test API keys
    provider, api_key = test_api_keys()
    if not provider:
        print("\n❌ Please set your API key first.")
        sys.exit(1)
    
    # Make sure provider matches package
    if provider == "openai" and provider_pkg != "openai":
        print("\n⚠️  Warning: OPENAI_API_KEY set but openai package not installed")
        print("  Install with: pip install openai")
        sys.exit(1)
    
    if provider == "anthropic" and provider_pkg != "anthropic":
        print("\n⚠️  Warning: ANTHROPIC_API_KEY set but anthropic package not installed")
        print("  Install with: pip install anthropic")
        sys.exit(1)
    
    # Test LLM scorer
    success = test_llm_scorer(provider, api_key)
    
    if success:
        print("\n" + "="*60)
        print("✅ All tests passed! You can now use:")
        print("   python experiments/visualize_with_llm.py")
        print("="*60)
        sys.exit(0)
    else:
        print("\n" + "="*60)
        print("❌ Tests failed. Please fix the issues above.")
        print("="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()

