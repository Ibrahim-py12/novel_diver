"""
Decision tracking and history management for Novel Diver - Interactive Fanfiction MVP

This module defines data structures for tracking story progress, decisions,
and maintaining session history.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import json

@dataclass
class StoryChunk:
    """
    Represents a single narrative segment in the story.
    
    Attributes:
        text: The narrative text content
        timestamp: When this chunk was generated
        chunk_id: Unique identifier for this chunk
        decision_options: Available options presented to the user (if any)
    """
    
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    chunk_id: str = field(default_factory=lambda: f"chunk_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    decision_options: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "chunk_id": self.chunk_id,
            "decision_options": self.decision_options
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryChunk":
        """Create from dictionary."""
        return cls(
            text=data["text"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            chunk_id=data["chunk_id"],
            decision_options=data.get("decision_options", [])
        )

@dataclass
class DecisionEntry:
    """
    Represents a decision made by the user.
    
    Attributes:
        decision_text: The text of the decision made
        options_available: All options that were presented
        chosen_index: Index of the chosen option
        timestamp: When the decision was made
    """
    
    decision_text: str
    options_available: List[str]
    chosen_index: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "decision_text": self.decision_text,
            "options_available": self.options_available,
            "chosen_index": self.chosen_index,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DecisionEntry":
        """Create from dictionary."""
        return cls(
            decision_text=data["decision_text"],
            options_available=data["options_available"],
            chosen_index=data["chosen_index"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

@dataclass
class StoryHistory:
    """
    Manages the complete history of a story session.
    
    Attributes:
        session_id: Unique identifier for this story session
        character_name: Name of the protagonist
        world_type: The world/genre of the story
        story_chunks: List of narrative segments
        decisions: List of user decisions
        created_at: When the session was started
        last_updated: When the session was last modified
    """
    
    session_id: str
    character_name: str
    world_type: str
    story_chunks: List[StoryChunk] = field(default_factory=list)
    decisions: List[DecisionEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def add_story_chunk(self, text: str, options: List[str] = None) -> StoryChunk:
        """
        Add a new story chunk to the history.
        
        Args:
            text: The narrative text
            options: Available decision options
            
        Returns:
            StoryChunk: The created story chunk
        """
        chunk = StoryChunk(
            text=text,
            decision_options=options or []
        )
        
        self.story_chunks.append(chunk)
        self.last_updated = datetime.now()
        return chunk
    
    def add_decision(self, decision_text: str, available_options: List[str], chosen_index: int) -> DecisionEntry:
        """
        Add a new decision to the history.
        
        Args:
            decision_text: The text of the chosen decision
            available_options: All options that were presented
            chosen_index: Index of the chosen option
            
        Returns:
            DecisionEntry: The created decision entry
        """
        decision = DecisionEntry(
            decision_text=decision_text,
            options_available=available_options,
            chosen_index=chosen_index
        )
        
        self.decisions.append(decision)
        self.last_updated = datetime.now()
        return decision
    
    def get_full_story_text(self) -> str:
        """
        Get the complete story text as a single string.
        
        Returns:
            str: The full narrative combined
        """
        story_parts = []
        
        for i, chunk in enumerate(self.story_chunks):
            story_parts.append(f"--- Chapter {i + 1} ---")
            story_parts.append(chunk.text)
            
            # Add decision if it exists
            if i < len(self.decisions):
                decision = self.decisions[i]
                story_parts.append(f"\n[Decision Made: {decision.decision_text}]\n")
        
        return "\n\n".join(story_parts)
    
    def get_recent_context(self, num_chunks: int = 3) -> str:
        """
        Get recent story context for AI continuation.
        
        Args:
            num_chunks: Number of recent chunks to include
            
        Returns:
            str: Recent story context
        """
        if not self.story_chunks:
            return ""
        
        recent_chunks = self.story_chunks[-num_chunks:]
        context_parts = []
        
        for chunk in recent_chunks:
            context_parts.append(chunk.text)
        
        # Add last decision if available
        if self.decisions and len(self.story_chunks) > len(self.decisions):
            last_decision = self.decisions[-1]
            context_parts.append(f"\n[Last Decision: {last_decision.decision_text}]")
        
        return "\n\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "character_name": self.character_name,
            "world_type": self.world_type,
            "story_chunks": [chunk.to_dict() for chunk in self.story_chunks],
            "decisions": [decision.to_dict() for decision in self.decisions],
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat()
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryHistory":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            character_name=data["character_name"],
            world_type=data["world_type"],
            story_chunks=[StoryChunk.from_dict(chunk_data) for chunk_data in data.get("story_chunks", [])],
            decisions=[DecisionEntry.from_dict(decision_data) for decision_data in data.get("decisions", [])],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"])
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "StoryHistory":
        """Create from JSON string."""
        data = json.loads(json_str)
        return cls.from_dict(data)
    
    def save_to_file(self, filepath: str) -> bool:
        """
        Save the story history to a file.
        
        Args:
            filepath: Path where to save the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.to_json())
            return True
        except Exception as e:
            print(f"Error saving to file: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str) -> Optional["StoryHistory"]:
        """
        Load story history from a file.
        
        Args:
            filepath: Path to the file
            
        Returns:
            StoryHistory: Loaded history or None if failed
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json_str = f.read()
            return cls.from_json(json_str)
        except Exception as e:
            print(f"Error loading from file: {e}")
            return None
    
    def __len__(self) -> int:
        """Return the number of story chunks."""
        return len(self.story_chunks)
