"""
Core story engine for Novel Diver - Interactive Fanfiction MVP

This module handles story generation, AI interactions, and prompt management
for creating dynamic interactive narratives.
"""

import os
import re
import random
from typing import List, Tuple, Optional
import requests
from pathlib import Path

from .character import Character
from .decision import StoryHistory
from config import get_client, config


class StoryEngine:
    """
    Main engine for generating interactive stories using AI.
    
    Handles prompt construction, AI API calls, and response parsing.
    """
    
    def __init__(self):
        self.client = None
        self.api_name = None
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Initialize AI client
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize the AI client."""
        # Check for demo mode first
        if os.getenv("DEMO_MODE") == "true":
            self.client = "demo"
            self.api_name = "demo"
            return
            
        try:
            self.client, self.api_name = get_client()
            if not self.client:
                raise Exception("No AI client available")
        except Exception as e:
            print(f"Failed to initialize AI client: {e}")
            self.client = None
            self.api_name = None
    
    def load_world_template(self, world_type: str) -> str:
        """
        Load world template from file.
        
        Args:
            world_type: The world type (cultivation, martial_arts, fantasy)
            
        Returns:
            str: World template content or default if not found
        """
        template_file = self.prompts_dir / f"{world_type}.txt"
        
        try:
            if template_file.exists():
                with open(template_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error loading world template: {e}")
        
        # Return default template if file not found
        return self._get_default_template(world_type)
    
    def _get_default_template(self, world_type: str) -> str:
        """Get a default world template if file loading fails."""
        defaults = {
            "cultivation": "A mystical world where people cultivate spiritual energy to gain power and transcend mortality.",
            "martial_arts": "A world of martial artists, honor duels, and ancient fighting techniques.",
            "fantasy": "A magical realm with wizards, dragons, and epic quests.",
            "sci_fi": "A futuristic universe with advanced technology and space exploration.",
            "modern_urban": "A modern city setting with hidden supernatural elements."
        }
        return defaults.get(world_type, defaults["fantasy"])
    
    def create_system_prompt(self, character: Character, world_template: str) -> str:
        """
        Create the system prompt for AI story generation.
        
        Args:
            character: The protagonist character
            world_template: World setting description
            
        Returns:
            str: Complete system prompt
        """
        
        system_prompt = f"""
You are a masterful interactive fiction writer creating an engaging story for the user. Follow these guidelines:

{world_template}

{character.to_prompt()}

STORY WRITING RULES:
1. Write in second person perspective ("You do...", "You see...") to immerse the protagonist
2. Create vivid, descriptive scenes that bring the world to life
3. Include dialogue from NPCs with distinct personalities
4. Generate unexpected twists and consequences based on previous decisions
5. Maintain consistency with the character's background and motivations
6. Each story segment should be 200-400 words

DECISION POINTS:
- After each story segment, create a decision point with exactly 4 options
- Options should be meaningfully different and lead to different outcomes
- Include at least one risky/bold option and one cautious option
- Make sure options align with the character's abilities and the world setting

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
[Story text goes here - 200-400 words describing the scene, action, and dialogue]

DECISION_POINT
1. [First option - brief but clear description]
2. [Second option - brief but clear description]  
3. [Third option - brief but clear description]
4. [Fourth option - brief but clear description]

Remember: The story should feel dynamic and reactive to the character's previous choices. Create memorable NPCs and situations that matter to the ongoing narrative.
"""
        
        return system_prompt.strip()
    
    def start_story(self, character: Character) -> Tuple[str, List[str]]:
        """
        Start a new story with the given character.
        
        Args:
            character: The protagonist character
            
        Returns:
            tuple: (story_text, decision_options)
        """
        
        if not self.client:
            return "Error: No AI client available. Please check your API configuration.", []
        
        # Load world template
        world_template = self.load_world_template(character.world)
        
        # Create system prompt
        system_prompt = self.create_system_prompt(character, world_template)
        
        # Create initial story prompt
        story_prompt = f"""
Begin an exciting {character.world} adventure. Introduce the protagonist {character.name} in an engaging opening scene that sets up their story. Include:

1. A vivid description of the initial setting
2. A situation that connects to their background: {character.background}
3. An immediate challenge or opportunity that relates to their goals: {character.goals}
4. At least one interesting NPC to interact with

Make the opening compelling and immersive, then present the first major decision point.
"""
        
        try:
            # Generate story
            response = self._generate_with_retry(system_prompt + "\n\n" + story_prompt)
            return self._parse_response(response)
            
        except Exception as e:
            print(f"Error generating story: {e}")
            return f"Error generating story: {str(e)}", []
    
    def continue_story(self, history: StoryHistory, chosen_option: str) -> Tuple[str, List[str]]:
        """
        Continue the story based on the chosen option.
        
        Args:
            history: The story history so far
            chosen_option: The option chosen by the user
            
        Returns:
            tuple: (story_text, decision_options)
        """
        
        if not self.client:
            return "Error: No AI client available. Please check your API configuration.", []
        
        # Get recent context
        recent_context = history.get_recent_context(num_chunks=3)
        
        # Create character from history (simplified)
        character = Character(
            name=history.character_name,
            world=history.world_type,
            background="", # We don't store this in history, but it's okay for continuation
            traits=[],
            goals=""
        )
        
        # Load world template
        world_template = self.load_world_template(history.world_type)
        
        # Create system prompt
        system_prompt = self.create_system_prompt(character, world_template)
        
        # Create continuation prompt
        continuation_prompt = f"""
PREVIOUS STORY CONTEXT:
{recent_context}

PLAYER'S CHOSEN ACTION:
{chosen_option}

Continue the story based on the player's choice. Show the consequences of their decision, advance the plot, and create a new compelling situation with 4 new decision options. Make sure the story flows naturally from the previous events and the chosen action.
"""
        
        try:
            # Generate continuation
            response = self._generate_with_retry(system_prompt + "\n\n" + continuation_prompt)
            return self._parse_response(response)
            
        except Exception as e:
            print(f"Error continuing story: {e}")
            return f"Error continuing story: {str(e)}", []
    
    def _generate_with_retry(self, prompt: str) -> str:
        """
        Generate text with retry logic.
        
        Args:
            prompt: The prompt to send to the AI
            
        Returns:
            str: Generated response
        """
        
        def generate_func():
            if self.api_name == "demo":
                return self._get_demo_response(prompt)
            
            elif self.api_name == "gemini":
                response = self.client.generate_content(prompt)
                return response.text
            
            elif self.api_name == "huggingface":
                # Use a good free model for text generation
                models_to_try = [
                    "mistralai/Mistral-7B-Instruct-v0.1",
                    "microsoft/DialoGPT-large",
                    "gpt2-large"
                ]
                
                headers = {"Authorization": f"Bearer {self.client['token']}"}
                
                for model in models_to_try:
                    try:
                        model_url = self.client["api_url"] + model
                        payload = {
                            "inputs": prompt,
                            "parameters": {
                                "max_new_tokens": 800,
                                "temperature": 0.7,
                                "top_p": 0.9,
                                "do_sample": True,
                                "return_full_text": False
                            }
                        }
                        
                        response = requests.post(model_url, headers=headers, json=payload, timeout=30)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if isinstance(result, list) and len(result) > 0:
                                generated = result[0].get("generated_text", "")
                                if generated and len(generated.strip()) > 50:
                                    return generated
                            elif isinstance(result, dict) and "generated_text" in result:
                                return result["generated_text"]
                    except Exception as e:
                        print(f"Model {model} failed: {e}")
                        continue
                
                # If all models fail, return an error message
                raise Exception("All Hugging Face models failed. Please try again or use a different API.")
            
            else:
                raise Exception(f"Unsupported API: {self.api_name}")
        
        # Use retry with backoff from config
        return config.retry_with_backoff(generate_func)
    
    def _parse_response(self, response: str) -> Tuple[str, List[str]]:
        """
        Parse AI response to extract story text and decision options.
        
        Args:
            response: Raw AI response
            
        Returns:
            tuple: (story_text, decision_options)
        """
        
        # Split on DECISION_POINT
        parts = response.split("DECISION_POINT")
        
        if len(parts) < 2:
            # Fallback: create some generic options if parsing fails
            return response.strip(), [
                "Continue cautiously",
                "Take a bold approach", 
                "Seek more information",
                "Try a creative solution"
            ]
        
        story_text = parts[0].strip()
        options_text = parts[1].strip()
        
        # Extract numbered options
        options = []
        for line in options_text.split('\n'):
            line = line.strip()
            # Match patterns like "1. option text" or "1) option text"
            match = re.match(r'^[1-4][\.\)]\s*(.+)', line)
            if match:
                options.append(match.group(1).strip())
        
        # Ensure we have exactly 4 options
        if len(options) < 4:
            options.extend([
                "Take a different approach",
                "Wait and observe", 
                "Act decisively",
                "Seek help from others"
            ][:4-len(options)])
        elif len(options) > 4:
            options = options[:4]
        
        return story_text, options
    
    def is_available(self) -> bool:
        """Check if the story engine is ready to use."""
        return self.client is not None and self.api_name is not None
    
    def _get_demo_response(self, prompt: str) -> str:
        """Generate demo responses for testing without API keys."""
        import random
        
        # Simple demo responses based on prompt content
        if "Begin an exciting" in prompt:
            # Starting story responses
            demo_stories = {
                "cultivation": """
You find yourself standing at the entrance of the Azure Mountain Sect, morning mist swirling around ancient stone pillars carved with mystical symbols. Elder Chen, a weathered man with kind eyes, approaches you with measured steps.

"Welcome, young one," he says, his voice carrying the weight of centuries. "I sense great potential within you. The spiritual energy here is dense - perfect for beginning your cultivation journey. However, the path ahead is treacherous. Three trials await new disciples."

He gestures toward three different paths leading up the mountain. The left path glows with a soft golden light, the middle path crackles with lightning energy, and the right path seems shrouded in mysterious shadows.

"Choose wisely," Elder Chen warns. "Each path will shape your cultivation foundation differently."

DECISION_POINT
1. Take the golden path of harmony and balance
2. Choose the lightning path of power and intensity
3. Enter the shadow path of mystery and stealth
4. Ask Elder Chen for more guidance about the paths
""",
                "fantasy": """
The ancient tavern door creaks open as you step into the dimly lit common room. The Prancing Pony is filled with an eclectic mix of travelers - hooded figures whispering in dark corners, jovial merchants sharing ales, and a lone bard strumming melancholic melodies by the fireplace.

Sudenly, a commotion erupts near the bar. A young woman with pointed ears and silver hair - clearly an elf - is arguing with a burly dwarf over a leather-bound map spread across the wooden surface.

"The Dragon's Hoard is real!" she insists, her emerald eyes flashing. "My grandfather's journal contains the exact location!"

The dwarf strokes his braided beard skeptically. "Aye, lass, and I'm the King of the Mountain Folk. That map's led many a fool to their doom."

They both notice you approaching and turn their attention your way. The elf's expression brightens with hope while the dwarf eyes you warily.

DECISION_POINT
1. Offer to help them decipher the map
2. Challenge the dwarf's skepticism about the treasure
3. Ask to hear more about the Dragon's Hoard legend
4. Order a drink and listen to their conversation quietly
""",
                "martial_arts": """
The morning sun filters through bamboo leaves as you practice your forms in the training courtyard of the Iron Fist School. Your muscles ache from months of rigorous training, but your master's words echo in your mind: "True strength comes not from the body, but from the spirit."

Suddenly, urgent shouts pierce the tranquil morning. Master Liu bursts through the gates, his usually calm demeanor replaced by barely controlled fury.

"They're gone," he announces grimly to the assembled students. "The Five Sacred Scrolls of our school have been stolen in the night. Without them, our martial arts tradition dies with this generation."

A fellow student, Wei, steps forward angrily. "Master, we must pursue the thieves immediately! Every moment we delay, they get further away!"

But another student, Mei, raises her hand thoughtfully. "Perhaps we should investigate the scene first. Rushing blindly could lead us into a trap."

Master Liu looks to you, his most promising student. "What do you counsel? Time is precious, but so is wisdom."

DECISION_POINT
1. Agree with Wei - pursue the thieves immediately
2. Support Mei's cautious approach to investigate first
3. Suggest splitting into two groups to do both
4. Ask Master Liu if he has any idea who might be responsible
"""
            }
            
            # Extract world type from prompt
            world = "fantasy"  # default
            if "cultivation" in prompt.lower():
                world = "cultivation"
            elif "martial" in prompt.lower():
                world = "martial_arts"
            elif "sci" in prompt.lower() or "futuristic" in prompt.lower():
                world = "sci_fi"
            elif "urban" in prompt.lower() or "modern" in prompt.lower():
                world = "modern_urban"
                
            return demo_stories.get(world, demo_stories["fantasy"])
        
        else:
            # Continuation responses
            continuations = [
                """
Your choice leads you down a winding path filled with unexpected encounters. As you move forward, the landscape around you shifts and changes, revealing new challenges and opportunities.

A mysterious figure emerges from the shadows, offering cryptic advice about the journey ahead. "Not all is as it seems," they whisper before vanishing again.

You notice three distinct paths branching before you, each promising different adventures and potential rewards.

DECISION_POINT
1. Take the path that leads toward distant mountains
2. Follow the river route through the valley
3. Venture into the dark forest ahead
4. Rest here and contemplate your next move
""",
                """
The consequences of your previous decision begin to unfold in ways you never expected. New allies emerge while old certainties crumble, forcing you to adapt and grow.

A wise mentor appears, offering valuable insights: "Every choice shapes not just your destination, but who you become along the way."

As the story progresses, you find yourself facing a crucial decision that could change everything.

DECISION_POINT
1. Trust your instincts and act boldly
2. Seek counsel from your companions
3. Take time to carefully analyze the situation
4. Try to find a creative alternative solution
""",
                """
Your journey takes an unexpected turn as new revelations come to light. The world around you proves more complex and fascinating than you initially imagined.

Characters you thought you understood reveal hidden depths, while new mysteries emerge that challenge everything you believed to be true.

Standing at this crossroads, you must decide how to proceed with this newfound knowledge.

DECISION_POINT
1. Embrace the change and adapt your approach
2. Hold firm to your original principles
3. Seek to understand the deeper truth
4. Focus on the immediate practical concerns
"""
            ]
            
            return random.choice(continuations)


# Global story engine instance
story_engine = StoryEngine()

def get_story_engine() -> StoryEngine:
    """Get the global story engine instance."""
    story_engine = StoryEngine()
    return story_engine
