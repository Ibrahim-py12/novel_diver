#!/usr/bin/env python3
"""
Simple test script for Novel Diver MVP

This script tests the basic functionality without requiring API keys.
"""

import sys
from pathlib import Path

# Add modules to path
sys.path.append(str(Path(__file__).parent))

from modules.character import Character
from modules.decision import StoryHistory, StoryChunk, DecisionEntry
from modules.story_engine import StoryEngine
from config import Config

def test_character_creation():
    """Test character creation and validation."""
    print("🧪 Testing Character Creation...")
    
    # Test valid character
    char = Character(
        name="Test Hero",
        background="A brave adventurer seeking their destiny in a magical world.",
        traits=["brave", "curious", "loyal"],
        goals="To find the legendary artifact and save their homeland.",
        world="fantasy"
    )
    
    is_valid, issues = char.validate()
    assert is_valid, f"Character validation failed: {issues}"
    
    # Test character prompt generation
    prompt = char.to_prompt()
    assert "Test Hero" in prompt
    assert "fantasy" in prompt.lower()
    
    # Test sample character creation
    sample = Character.create_sample("cultivation")
    assert sample.world == "cultivation"
    assert len(sample.traits) > 0
    
    print("✅ Character creation tests passed!")

def test_story_history():
    """Test story history management."""
    print("🧪 Testing Story History...")
    
    history = StoryHistory(
        session_id="test_session",
        character_name="Test Hero", 
        world_type="fantasy"
    )
    
    # Add a story chunk
    chunk = history.add_story_chunk(
        "You find yourself in a dark forest...",
        ["Go left", "Go right", "Climb a tree", "Call for help"]
    )
    
    assert len(history.story_chunks) == 1
    assert chunk.text == "You find yourself in a dark forest..."
    
    # Add a decision
    decision = history.add_decision(
        "Go left", 
        ["Go left", "Go right", "Climb a tree", "Call for help"],
        0
    )
    
    assert len(history.decisions) == 1
    assert decision.decision_text == "Go left"
    
    # Test context retrieval
    context = history.get_recent_context()
    assert "dark forest" in context
    
    # Test serialization
    json_str = history.to_json()
    assert "test_session" in json_str
    
    # Test deserialization
    restored = StoryHistory.from_json(json_str)
    assert restored.session_id == history.session_id
    assert len(restored.story_chunks) == 1
    
    print("✅ Story history tests passed!")

def test_configuration():
    """Test configuration and API detection."""
    print("🧪 Testing Configuration...")
    
    config = Config()
    print(f"Available APIs: {config.available_apis}")
    
    if not config.available_apis:
        print("⚠️  No API keys detected - this is normal for testing")
        print("   Set GEMINI_API_KEY or HUGGINGFACE_TOKEN to test with real AI")
    
    print("✅ Configuration tests passed!")

def test_story_engine():
    """Test story engine (without API calls)."""
    print("🧪 Testing Story Engine...")
    
    engine = StoryEngine()
    
    # Test world template loading
    template = engine.load_world_template("fantasy")
    assert "fantasy" in template.lower() or "magical" in template.lower()
    
    # Test system prompt creation
    char = Character.create_sample("fantasy")
    system_prompt = engine.create_system_prompt(char, template)
    assert char.name in system_prompt
    assert "DECISION_POINT" in system_prompt
    
    # Test response parsing
    mock_response = """
You enter a magical forest filled with glowing mushrooms and singing birds.
The path ahead splits into three directions.

DECISION_POINT
1. Take the left path toward the mountain
2. Take the right path toward the river  
3. Go straight into the dense woods
4. Set up camp and rest first
"""
    
    story_text, options = engine._parse_response(mock_response)
    assert "magical forest" in story_text
    assert len(options) == 4
    assert "Take the left path" in options[0]
    
    print("✅ Story engine tests passed!")

def run_all_tests():
    """Run all tests."""
    print("🚀 Starting Novel Diver MVP Tests...\n")
    
    try:
        test_character_creation()
        test_story_history()
        test_configuration()
        test_story_engine()
        
        print("\n🎉 All tests passed! The MVP is ready to run.")
        print("\n📋 To start the application:")
        print("   streamlit run app.py")
        print("\n🔑 Don't forget to set your API key:")
        print("   set GEMINI_API_KEY=your_key_here")
        print("   or")
        print("   set HUGGINGFACE_TOKEN=your_token_here")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
