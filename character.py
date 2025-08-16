"""
Character data model for Novel Diver - Interactive Fanfiction MVP

This module defines the Character dataclass for storing protagonist information
and converting it to prompt-friendly format.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Character:
    """
    Character dataclass for storing protagonist information.
    
    Attributes:
        name: Character's name
        background: Character's backstory and origin
        traits: List of personality traits and characteristics
        goals: Character's main objectives and motivations
        world: The world/genre the character belongs to
    """
    
    name: str
    background: str
    traits: List[str]
    goals: str
    world: str
    
    def to_prompt(self) -> str:
        """
        Convert character information to a prompt-friendly format.
        
        Returns:
            str: Formatted character description for AI prompts
        """
        
        traits_str = ", ".join(self.traits) if self.traits else "No specific traits defined"
        
        prompt = f"""
PROTAGONIST PROFILE:
Name: {self.name}
World: {self.world.title()}
Background: {self.background}
Personality Traits: {traits_str}
Goals & Motivations: {self.goals}

This character is the protagonist of the story. All narrative should be written from their perspective or about their actions and decisions.
"""
        
        return prompt.strip()
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate character data and return any issues.
        
        Returns:
            tuple: (is_valid, list_of_issues)
        """
        
        issues = []
        
        if not self.name or len(self.name.strip()) < 2:
            issues.append("Name must be at least 2 characters long")
        
        if not self.background or len(self.background.strip()) < 10:
            issues.append("Background must be at least 10 characters long")
        
        if not self.goals or len(self.goals.strip()) < 10:
            issues.append("Goals must be at least 10 characters long")
        
        if not self.world:
            issues.append("World must be specified")
        
        # Check for reasonable length limits
        if len(self.name) > 100:
            issues.append("Name is too long (max 100 characters)")
        
        if len(self.background) > 1000:
            issues.append("Background is too long (max 1000 characters)")
        
        if len(self.goals) > 500:
            issues.append("Goals are too long (max 500 characters)")
        
        return len(issues) == 0, issues
    
    @classmethod
    def create_sample(cls, world: str) -> "Character":
        """
        Create a sample character for testing purposes.
        
        Args:
            world: The world type for the character
            
        Returns:
            Character: A sample character instance
        """
        
        samples = {
            "cultivation": cls(
                name="Li Wei",
                background="A young orphan discovered to have rare spiritual roots, taken in by the Azure Mountain Sect after showing promise in cultivation.",
                traits=["Determined", "Humble", "Quick-learner", "Loyal"],
                goals="To avenge his deceased master and reach the peak of cultivation to protect those he cares about.",
                world="cultivation"
            ),
            "martial_arts": cls(
                name="Chen Ming",
                background="The last surviving student of the destroyed Iron Fist School, wandering the jianghu to restore his school's honor.",
                traits=["Honorable", "Skilled fighter", "Seeking justice", "Stubborn"],
                goals="To find and defeat the masked warriors who destroyed his school and master.",
                world="martial_arts"
            ),
            "fantasy": cls(
                name="Aria Nightwhisper",
                background="A half-elf mage apprentice who discovered an ancient spellbook in her village's ruins after a dragon attack.",
                traits=["Curious", "Brave", "Magically gifted", "Compassionate"],
                goals="To master the ancient magic and prevent the return of the dark dragon lord.",
                world="fantasy"
            )
        }
        
        return samples.get(world, samples["fantasy"])
    
    def __str__(self) -> str:
        """String representation of the character."""
        return f"{self.name} ({self.world.title()} World)"
