"""
Novel Diver - Interactive Fanfiction MVP
Main Streamlit Application with User Authentication and Story Pagination

An interactive fanfiction application where users become protagonists in dynamic stories.
Now with user accounts, story saving, and paginated story display.
"""

import streamlit as st
import uuid
import json
from datetime import datetime
from pathlib import Path

from character import Character
from decision import StoryHistory
from story_engine import get_story_engine
from config import validate_and_set_api_key, config
from auth import auth
import os

# Page configuration
st.set_page_config(
    page_title="Novel Diver - Interactive Fanfiction",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Available worlds
WORLDS = {
    "cultivation": "🧘 Cultivation World",
    "martial_arts": "🥋 Martial Arts World",
    "fantasy": "🧙 Fantasy World",
    "sci_fi": "🚀 Sci-Fi World",
    "modern_urban": "🏙️ Modern Urban Fantasy"
}

def initialize_session_state():
    """Initialize session state variables."""
    # Authentication state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "user_data" not in st.session_state:
        st.session_state.user_data = None

    if "show_auth_form" not in st.session_state:
        st.session_state.show_auth_form = "login"  # "login" or "register"

    # Story state
    if "story_history" not in st.session_state:
        st.session_state.story_history = None

    if "current_character" not in st.session_state:
        st.session_state.current_character = None

    if "current_options" not in st.session_state:
        st.session_state.current_options = []

    if "story_started" not in st.session_state:
        st.session_state.story_started = False

    if "waiting_for_choice" not in st.session_state:
        st.session_state.waiting_for_choice = False

    if "api_configured" not in st.session_state:
        st.session_state.api_configured = False

    if "validation_in_progress" not in st.session_state:
        st.session_state.validation_in_progress = False

    # Character creation state
    if "show_character_form" not in st.session_state:
        st.session_state.show_character_form = True

    # Error handling
    if "last_story_error" not in st.session_state:
        st.session_state.last_story_error = None

    # Pagination state
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1

    if "chapters_per_page" not in st.session_state:
        st.session_state.chapters_per_page = 3

    # Story management
    if "current_story_id" not in st.session_state:
        st.session_state.current_story_id = None

    if "user_stories_list" not in st.session_state:
        st.session_state.user_stories_list = []

def check_authentication():
    """Check if user is authenticated via session."""
    if not st.session_state.authenticated:
        # Check for existing session
        if "session_id" in st.session_state:
            user_data = auth.validate_session(st.session_state.session_id)
            if user_data:
                st.session_state.authenticated = True
                st.session_state.user_data = user_data
                return True

    return st.session_state.authenticated

def display_auth_forms():
    """Display login and registration forms."""
    st.title("🔐 Welcome to Novel Diver")
    st.subheader("Create an account to save your adventures!")

    # Toggle between login and register
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔑 Login", use_container_width=True):
            st.session_state.show_auth_form = "login"
    with col2:
        if st.button("📝 Register", use_container_width=True):
            st.session_state.show_auth_form = "register"

    st.markdown("---")

    if st.session_state.show_auth_form == "login":
        display_login_form()
    else:
        display_register_form()

    # Guest option
    st.markdown("---")
    st.markdown("### 🎮 Or Continue as Guest")
    st.info("⚠️ **Note:** Stories created as guest will be lost when you close the app.")
    if st.button("🚶 Continue as Guest", type="secondary"):
        st.session_state.authenticated = True
        st.session_state.user_data = {"username": "Guest", "user_id": "guest"}
        st.rerun()

def display_login_form():
    """Display the login form."""
    st.markdown("### 🔑 Login to Your Account")

    with st.form("login_form"):
        username = st.text_input("Username or Email", placeholder="Enter your username or email")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        submitted = st.form_submit_button("🔑 Login", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.error("Please fill in both username/email and password")
                return

            with st.spinner("Logging in..."):
                success, message, user_data = auth.login_user(username, password)

                if success:
                    st.success(message)
                    st.session_state.authenticated = True
                    st.session_state.user_data = user_data
                    st.session_state.session_id = user_data["session_id"]
                    st.rerun()
                else:
                    st.error(message)

def display_register_form():
    """Display the registration form."""
    st.markdown("### 📝 Create New Account")

    with st.form("register_form"):
        username = st.text_input("Username", placeholder="Choose a unique username (min 3 characters)")
        email = st.text_input("Email", placeholder="Enter your email address")
        password = st.text_input("Password", type="password", placeholder="Create a password (min 6 characters)")
        confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")

        submitted = st.form_submit_button("📝 Create Account", type="primary", use_container_width=True)

        if submitted:
            if not all([username, email, password, confirm_password]):
                st.error("Please fill in all fields")
                return

            if password != confirm_password:
                st.error("Passwords do not match")
                return

            with st.spinner("Creating account..."):
                success, message = auth.register_user(username, email, password)

                if success:
                    st.success(message)
                    st.info("You can now login with your new account!")
                    st.session_state.show_auth_form = "login"
                    st.rerun()
                else:
                    st.error(message)

def display_user_profile():
    """Display user profile and story management in sidebar."""
    if not st.session_state.authenticated or not st.session_state.user_data:
        return

    user_data = st.session_state.user_data

    st.sidebar.header(f"👤 Welcome, {user_data['username']}!")

    # Logout button
    if st.sidebar.button("🚪 Logout"):
        if "session_id" in st.session_state:
            auth.logout_user(st.session_state.session_id)
        st.session_state.authenticated = False
        st.session_state.user_data = None
        st.session_state.session_id = None
        st.session_state.story_history = None
        st.session_state.current_character = None
        st.session_state.story_started = False
        st.rerun()

    # Story management for registered users
    if user_data.get("user_id") != "guest":
        st.sidebar.markdown("---")
        st.sidebar.header("📚 Your Stories")

        # Load user stories
        if not st.session_state.user_stories_list:
            st.session_state.user_stories_list = auth.get_user_stories(user_data["user_id"])

        # Display user stories
        if st.session_state.user_stories_list:
            story_options = {}
            for story in st.session_state.user_stories_list:
                title = f"{story['story_title']} ({story['character_name']})"
                story_options[title] = story

            selected_story_title = st.sidebar.selectbox(
                "Load a saved story:",
                options=[""] + list(story_options.keys()),
                key="story_selector"
            )

            if selected_story_title and st.sidebar.button("📖 Load Story"):
                load_user_story(story_options[selected_story_title])
        else:
            st.sidebar.info("No saved stories yet. Create your first adventure!")

        # Refresh stories button
        if st.sidebar.button("🔄 Refresh Stories"):
            st.session_state.user_stories_list = auth.get_user_stories(user_data["user_id"])
            st.rerun()

def load_user_story(story_info):
    """Load a user's saved story."""
    user_id = st.session_state.user_data["user_id"]
    story_data = auth.load_user_story(user_id, story_info["story_id"])

    if story_data:
        try:
            # Load story history from JSON
            history = StoryHistory.from_json(story_data)
            st.session_state.story_history = history
            st.session_state.current_story_id = story_info["story_id"]
            st.session_state.story_started = True
            st.session_state.show_character_form = False

            # Set up story state
            if history.story_chunks:
                last_chunk = history.story_chunks[-1]
                st.session_state.current_options = last_chunk.decision_options
                st.session_state.waiting_for_choice = bool(last_chunk.decision_options)

            # Create character object for display
            st.session_state.current_character = Character(
                name=history.character_name,
                world=history.world_type,
                background=f"Loaded character from saved story",
                traits=[],
                goals=""
            )

            st.success(f"📖 Loaded story: {story_info['story_title']}")
            st.rerun()

        except Exception as e:
            st.error(f"Failed to load story: {e}")

def save_current_story():
    """Save the current story to the database."""
    if not st.session_state.story_history or st.session_state.user_data.get("user_id") == "guest":
        return

    user_id = st.session_state.user_data["user_id"]
    story_data = st.session_state.story_history.to_json()
    story_title = f"{st.session_state.story_history.character_name}'s Adventure"
    character_name = st.session_state.story_history.character_name
    world_type = st.session_state.story_history.world_type

    if st.session_state.current_story_id:
        # Update existing story
        success = auth.update_user_story(user_id, st.session_state.current_story_id, story_data)
        if success:
            st.success("💾 Story updated successfully!")
        else:
            st.error("Failed to update story")
    else:
        # Save new story
        success, message = auth.save_user_story(
            user_id, story_data, story_title, character_name, world_type
        )
        if success:
            st.success(message)
            # Refresh story list
            st.session_state.user_stories_list = auth.get_user_stories(user_id)
        else:
            st.error(message)

def setup_api_configuration():
    """Create API configuration interface."""
    st.sidebar.header("🔧 API Configuration")

    # Check if API keys are already validated
    config.refresh_api_keys()  # Refresh to get latest keys

    if config.available_apis:
        st.sidebar.success(f"✅ API connected: {', '.join(config.available_apis).upper()}")
        if st.sidebar.button("🔄 Reset API Configuration"):
            # Clear environment variables and cache
            for key in ["GEMINI_API_KEY", "HUGGINGFACE_TOKEN", "OPENAI_API_KEY", "DEMO_MODE"]:
                os.environ.pop(key, None)
            config.clear_cache()
            config.refresh_api_keys()
            st.session_state.api_configured = False
            st.rerun()
        st.session_state.api_configured = True
        return True

    # Show current connection status
    if st.session_state.api_configured:
        st.sidebar.success("✅ AI Provider Connected!")
        if st.sidebar.button("🔄 Change API Provider"):
            st.session_state.api_configured = False
            os.environ.pop("DEMO_MODE", None)
            config.clear_cache()
            st.rerun()
        return True

    st.sidebar.markdown("""
    **🚀 Quick Setup - Choose your AI provider:**
    
    🥇 **Gemini 1.5 Flash** - Best free choice!  
    🥈 **Hugging Face** - Completely free  
    🥉 **OpenAI** - Premium quality (paid)  
    """)

    # API provider selection
    api_provider = st.sidebar.selectbox(
        "🤖 Select AI Provider:",
        options=[
            "👆 Choose an AI provider...",
            "🥇 Google Gemini 1.5 Flash (Free & Fast)",
            "🥈 Hugging Face (Free)",
            "🥉 OpenAI (Paid)",
            "🎮 Demo Mode (No API needed)"
        ],
        key="api_provider_select"
    )

    if api_provider == "🥇 Google Gemini 1.5 Flash (Free & Fast)":
        st.sidebar.markdown("""  
        **🎯 Get your FREE API key:**  
        👉 [aistudio.google.com](https://aistudio.google.com/app/apikey)  
        """)

        api_key = st.sidebar.text_input(
            "🔑 Paste your Gemini API Key:",
            type="password",
            placeholder="AIza... (paste your key here)",
            key="gemini_key_input",
            help="Your API key starts with 'AIza' and is about 39 characters long"
        )

        if api_key and len(api_key) > 10:
            if st.sidebar.button("✅ Validate & Connect", type="primary"):
                with st.spinner("🔍 Validating Gemini API key..."):
                    st.session_state.validation_in_progress = True
                    is_valid, message = validate_and_set_api_key("gemini", api_key)
                    st.session_state.validation_in_progress = False

                    if is_valid:
                        st.sidebar.success(message)
                        st.session_state.api_configured = True
                        st.rerun()
                    else:
                        st.sidebar.error(message)

    elif api_provider == "🥈 Hugging Face (Free)":
        st.sidebar.markdown("""  
        **🆓 Get your FREE token:**  
        👉 [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)  
        """)

        api_key = st.sidebar.text_input(
            "🔑 Paste your HF Token:",
            type="password",
            placeholder="hf_... (paste your token here)",
            key="hf_key_input",
            help="Your token starts with 'hf_' and is about 37 characters long"
        )

        if api_key and len(api_key) > 10:
            if st.sidebar.button("✅ Validate & Connect", type="primary"):
                with st.sidebar.spinner("🔍 Validating Hugging Face token..."):
                    st.session_state.validation_in_progress = True
                    is_valid, message = validate_and_set_api_key("huggingface", api_key)
                    st.session_state.validation_in_progress = False

                    if is_valid:
                        st.sidebar.success(message)
                        st.session_state.api_configured = True
                        st.rerun()
                    else:
                        st.sidebar.error(message)

    elif api_provider == "🥉 OpenAI (Paid)":
        st.sidebar.markdown("""  
        **💳 Get your API key (paid service):**  
        👉 [platform.openai.com/api-keys](https://platform.openai.com/api-keys)  
        """)

        api_key = st.sidebar.text_input(
            "🔑 Paste your OpenAI API Key:",
            type="password",
            placeholder="sk-... (paste your key here)",
            key="openai_key_input",
            help="Your key starts with 'sk-' and is about 51 characters long"
        )

        if api_key and len(api_key) > 10:
            if st.sidebar.button("✅ Validate & Connect", type="primary"):
                with st.sidebar.spinner("🔍 Validating OpenAI API key..."):
                    st.session_state.validation_in_progress = True
                    is_valid, message = validate_and_set_api_key("openai", api_key)
                    st.session_state.validation_in_progress = False

                    if is_valid:
                        st.sidebar.success(message)
                        st.session_state.api_configured = True
                        st.rerun()
                    else:
                        st.sidebar.error(message)

    elif api_provider == "🎮 Demo Mode (No API needed)":
        st.sidebar.markdown("""  
        **🎮 Demo Mode Active!**  
        
        ✅ Try the app with sample stories  
        ✅ No API key required  
        ✅ Experience all features  
        
        📝 **Note:** Stories are pre-written examples, not AI-generated.
        """)

        if st.sidebar.button("🎮 Activate Demo Mode"):
            os.environ["DEMO_MODE"] = "true"
            st.session_state.api_configured = True
            st.rerun()

    return False

def create_character_form():
    """Create the character creation form in the sidebar."""
    if not st.session_state.show_character_form:
        return None

    st.sidebar.header("🎭 Create Your Character")

    with st.sidebar.form("character_form"):
        selected_world_key = st.selectbox(
            "Choose Your World:",
            options=list(WORLDS.keys()),
            format_func=lambda x: WORLDS[x],
            key="world_select"
        )

        character_name = st.text_input(
            "Character Name:",
            placeholder="Enter your protagonist's name",
            key="char_name"
        )

        character_background = st.text_area(
            "Character Background:",
            placeholder="Describe your character's history, origin, and past experiences...",
            height=100,
            key="char_background"
        )

        traits_input = st.text_input(
            "Personality Traits:",
            placeholder="brave, curious, stubborn, kind (comma-separated)",
            key="char_traits"
        )

        character_goals = st.text_area(
            "Goals & Motivations:",
            placeholder="What does your character want to achieve? What drives them?",
            height=80,
            key="char_goals"
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Create Character", type="primary")
        with col2:
            use_sample = st.form_submit_button("📋 Use Sample")

    if use_sample:
        sample = Character.create_sample(selected_world_key)
        st.session_state.sample_character = sample
        st.sidebar.success(f"✨ Sample character created: **{sample.name}**")
        st.sidebar.info("👆 Click 'Use Sample' again to load the character into the form!")
        return None

    if hasattr(st.session_state, 'sample_character') and not any([character_name, character_background, traits_input, character_goals]):
        sample = st.session_state.sample_character
        character_name = sample.name
        character_background = sample.background
        traits_input = ", ".join(sample.traits)
        character_goals = sample.goals
        delattr(st.session_state, 'sample_character')

    if submitted:
        if not all([character_name, character_background, character_goals]):
            st.sidebar.error("❌ Please fill in all required fields!")
            return None

        traits = [trait.strip() for trait in traits_input.split(",") if trait.strip()] if traits_input else []

        character = Character(
            name=character_name,
            background=character_background,
            traits=traits,
            goals=character_goals,
            world=selected_world_key
        )

        is_valid, issues = character.validate()

        if not is_valid:
            st.sidebar.error("❌ Please fix these issues:")
            for issue in issues:
                st.sidebar.write(f"• {issue}")
            return None

        st.session_state.current_character = character
        st.session_state.show_character_form = False
        st.sidebar.success(f"✅ Character **{character.name}** created successfully!")
        st.rerun()

    return None

def display_paginated_story():
    """Display story with pagination for better readability."""
    if not st.session_state.story_history:
        if st.session_state.current_character:
            st.info(f"👤 Character ready: **{st.session_state.current_character.name}** | Click 'Start Adventure' below!")
        else:
            st.info("👈 Create your character in the sidebar to begin your adventure!")
        return

    history = st.session_state.story_history
    total_chapters = len(history.story_chunks)

    if total_chapters == 0:
        return

    # Story header
    st.title(f"📖 {history.character_name}'s Adventure")
    st.caption(f"World: {WORLDS[history.world_type]} | Started: {history.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Pagination controls
    chapters_per_page = st.session_state.chapters_per_page
    total_pages = (total_chapters - 1) // chapters_per_page + 1
    current_page = st.session_state.current_page

    # Ensure current page is valid
    if current_page > total_pages:
        st.session_state.current_page = total_pages
        current_page = total_pages
    if current_page < 1:
        st.session_state.current_page = 1
        current_page = 1

    # Page navigation
    if total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

        with col1:
            if st.button("⏮️ First", disabled=(current_page == 1)):
                st.session_state.current_page = 1
                st.rerun()

        with col2:
            if st.button("◀️ Prev", disabled=(current_page == 1)):
                st.session_state.current_page = current_page - 1
                st.rerun()

        with col3:
            st.markdown(f"<div style='text-align: center; padding: 0.25rem 0;'><strong>Page {current_page} of {total_pages}</strong></div>", unsafe_allow_html=True)

        with col4:
            if st.button("Next ▶️", disabled=(current_page == total_pages)):
                st.session_state.current_page = current_page + 1
                st.rerun()

        with col5:
            if st.button("Last ⏭️", disabled=(current_page == total_pages)):
                st.session_state.current_page = total_pages
                st.rerun()

    # Display chapters for current page
    start_idx = (current_page - 1) * chapters_per_page
    end_idx = min(start_idx + chapters_per_page, total_chapters)

    for i in range(start_idx, end_idx):
        chunk = history.story_chunks[i]
        st.markdown("---")
        st.markdown(f"### Chapter {i + 1}")
        st.markdown(chunk.text)

        # Show decision if it was made
        if i < len(history.decisions):
            decision = history.decisions[i]
            st.markdown(f"**🎯 Decision Made:** {decision.decision_text}")

    # Auto-scroll to latest chapter if on last page and waiting for choice
    if current_page == total_pages and st.session_state.waiting_for_choice:
        # Decision making interface
        if st.session_state.current_options:
            st.markdown("---")
            st.markdown("### 🤔 What will you do next?")

            choice = st.radio(
                "Choose your action:",
                options=range(len(st.session_state.current_options)),
                format_func=lambda x: f"{x + 1}. {st.session_state.current_options[x]}",
                key="decision_choice"
            )

            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("✅ Make Decision", type="primary"):
                    make_decision(choice)

            with col2:
                if st.button("🔄 Restart Story"):
                    restart_story()

    # Add quick jump to latest chapter button if not on last page
    if current_page < total_pages and total_chapters > chapters_per_page:
        if st.button(f"🚀 Jump to Latest Chapter ({total_chapters})", key="jump_to_latest"):
            st.session_state.current_page = total_pages
            st.rerun()

def make_decision(choice_index: int):
    """Process the user's decision and continue the story."""
    if not st.session_state.current_options or choice_index >= len(st.session_state.current_options):
        st.error("Invalid choice selected.")
        return

    chosen_option = st.session_state.current_options[choice_index]

    st.session_state.story_history.add_decision(
        decision_text=chosen_option,
        available_options=st.session_state.current_options,
        chosen_index=choice_index
    )

    with st.spinner("🤖 Generating next part of your story..."):
        engine = get_story_engine()

        if not engine.is_available():
            st.error("❌ Story engine is not available. Please check your API configuration.")
            if not config.available_apis:
                st.error("No valid API keys found. Please reconfigure your API in the sidebar.")
                st.info("💡 **Tip:** Check the sidebar to reconfigure your API key")
            return

        try:
            story_text, new_options = engine.continue_story(
                st.session_state.story_history,
                chosen_option
            )

            st.session_state.story_history.add_story_chunk(story_text, new_options)
            st.session_state.current_options = new_options
            st.session_state.waiting_for_choice = True

            # Auto-save for registered users
            if st.session_state.user_data and st.session_state.user_data.get("user_id") != "guest":
                save_current_story()

            # Jump to the latest page to show new content
            total_chapters = len(st.session_state.story_history.story_chunks)
            total_pages = (total_chapters - 1) // st.session_state.chapters_per_page + 1
            st.session_state.current_page = total_pages

            st.session_state.last_story_error = None
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            st.session_state.last_story_error = error_msg

            if "API key not valid" in error_msg or "API_KEY_INVALID" in error_msg:
                st.error("❌ **API Key Error:** Your API key is invalid or has expired.")
                st.info("💡 **Fix:** Go to the sidebar and update your API key")
            elif "quota" in error_msg.lower() or "limit" in error_msg.lower():
                st.error("❌ **Quota Exceeded:** Your API usage limit has been reached.")
                st.info("💡 Try again later or use a different API provider in the sidebar.")
            elif "403" in error_msg:
                st.error("❌ **Access Forbidden:** Your API key doesn't have the required permissions.")
                st.info("💡 **Fix:** Check your API key permissions or generate a new one")
            else:
                st.error(f"❌ **Error generating story:** {error_msg}")
                st.info("💡 This might be a temporary issue. Try the retry button below.")

            if st.button("🔄 Retry Last Action", key="retry_make_decision"):
                st.session_state.last_story_error = None
                make_decision(choice_index)

def start_new_story(character: Character):
    """Start a new story with the given character."""
    with st.spinner("🌟 Starting your adventure..."):
        config.refresh_api_keys()

        session_id = f"{character.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        st.session_state.story_history = StoryHistory(
            session_id=session_id,
            character_name=character.name,
            world_type=character.world
        )

        # Reset story ID for new story
        st.session_state.current_story_id = None

        engine = get_story_engine()

        if hasattr(engine, '_initialize_client'):
            try:
                engine._initialize_client()
            except Exception as e:
                st.error(f"Failed to reinitialize story engine: {e}")

        if not engine.is_available():
            st.error("❌ **Story engine is not available.**")
            if not config.available_apis and not os.getenv("DEMO_MODE"):
                st.error("**No valid API keys found.**")
                st.info("Please reconfigure your API key in the sidebar")
                st.info("💡 **Tip:** Check the sidebar to configure your API")
            return

        try:
            story_text, options = engine.start_story(character)

            st.session_state.story_history.add_story_chunk(story_text, options)
            st.session_state.current_options = options
            st.session_state.story_started = True
            st.session_state.waiting_for_choice = True
            st.session_state.current_page = 1  # Start at first page

            # Auto-save for registered users
            if st.session_state.user_data and st.session_state.user_data.get("user_id") != "guest":
                save_current_story()

            st.session_state.last_story_error = None
            st.rerun()

        except Exception as e:
            error_msg = str(e)
            st.session_state.last_story_error = error_msg
            st.error(f"❌ **Error starting story:** {error_msg}")

            if st.button("🔄 Retry Starting Story", key="retry_start_story"):
                config.clear_cache()
                config.refresh_api_keys()
                start_new_story(character)

def restart_story():
    """Restart the story from the beginning."""
    st.session_state.story_history = None
    st.session_state.current_options = []
    st.session_state.story_started = False
    st.session_state.waiting_for_choice = False
    st.session_state.last_story_error = None
    st.session_state.current_page = 1
    st.session_state.current_story_id = None
    st.session_state.show_character_form = False
    st.rerun()

def create_new_character():
    """Allow user to create a completely new character."""
    st.session_state.current_character = None
    st.session_state.show_character_form = True
    st.session_state.story_history = None
    st.session_state.story_started = False
    st.session_state.waiting_for_choice = False
    st.session_state.last_story_error = None
    st.session_state.current_page = 1
    st.session_state.current_story_id = None
    st.rerun()

def main():
    """Main application function."""
    initialize_session_state()

    # Check authentication
    if not check_authentication():
        display_auth_forms()
        return

    # User is authenticated - show main app
    st.title("📚 Novel Diver")
    st.subheader("Interactive Fanfiction Adventure")
    st.markdown("*Become the protagonist of your own story. Your choices shape the narrative.*")

    # Display user profile in sidebar
    display_user_profile()

    # API Configuration
    api_ready = setup_api_configuration()

    if not api_ready and not st.session_state.current_character:
        st.markdown("---")
        st.info("👈 **Please configure your AI API in the sidebar to get started!**")

        st.markdown("### 🤖 Why do I need an API key?")
        st.markdown("""
        Novel Diver uses AI to generate your interactive stories. Choose from these providers:
        
        **🥇 Recommended: Google Gemini 1.5 Flash**
        - ✅ **Completely free** with generous daily limits
        - ✅ **Super fast** responses  
        - ✅ **High-quality** story generation
        
        **🥈 Alternative: Hugging Face**
        - ✅ **Completely free** forever
        - ⚠️ Response quality may vary
        
        **🥉 Advanced: OpenAI**
        - ⚠️ **Paid service** (pay per use)
        - ✅ Excellent and consistent quality
        """)

        st.markdown("### 🎮 Or Try Demo Mode")
        st.info("Want to test the app first? Use **Demo Mode** in the sidebar - no API key needed!")
        return

    # Show API status
    if config.available_apis and not os.getenv("DEMO_MODE"):
        st.success(f"🤖 **AI Connected:** {', '.join(config.available_apis).upper()}")
    elif os.getenv("DEMO_MODE"):
        st.info("🎮 **Demo Mode Active** - Using sample stories")

    # Sidebar content based on current state
    if st.session_state.current_character and not st.session_state.show_character_form:
        st.sidebar.header("👤 Current Character")
        char = st.session_state.current_character
        st.sidebar.markdown(f"**Name:** {char.name}")
        st.sidebar.markdown(f"**World:** {WORLDS[char.world]}")
        st.sidebar.markdown(f"**Background:** {char.background[:100]}...")

        if st.sidebar.button("🎭 Create New Character"):
            create_new_character()
    else:
        create_character_form()

    # Story controls in sidebar
    if st.session_state.story_started:
        st.sidebar.markdown("---")
        st.sidebar.header("📊 Story Controls")

        # Manual save button for registered users
        if st.session_state.user_data and st.session_state.user_data.get("user_id") != "guest":
            if st.sidebar.button("💾 Save Story"):
                save_current_story()

        if st.sidebar.button("🔄 Restart Adventure"):
            restart_story()

        # Pagination settings
        st.sidebar.markdown("**📄 Page Settings:**")
        new_chapters_per_page = st.sidebar.selectbox(
            "Chapters per page:",
            options=[1, 2, 3, 5, 10],
            index=2,  # Default to 3
            key="chapters_per_page_selector"
        )

        if new_chapters_per_page != st.session_state.chapters_per_page:
            st.session_state.chapters_per_page = new_chapters_per_page
            # Recalculate current page
            if st.session_state.story_history:
                total_chapters = len(st.session_state.story_history.story_chunks)
                total_pages = (total_chapters - 1) // new_chapters_per_page + 1
                if st.session_state.current_page > total_pages:
                    st.session_state.current_page = total_pages
            st.rerun()

        # Story stats
        if st.session_state.story_history:
            history = st.session_state.story_history
            st.sidebar.markdown("**Story Stats:**")
            st.sidebar.write(f"📖 Chapters: {len(history.story_chunks)}")
            st.sidebar.write(f"🎯 Decisions: {len(history.decisions)}")

            total_words = sum(len(chunk.text.split()) for chunk in history.story_chunks)
            st.sidebar.write(f"📝 Words: {total_words:,}")

    # Main area
    col1, col2 = st.columns([3, 1])

    with col1:
        if st.session_state.story_started:
            display_paginated_story()
        elif st.session_state.current_character and not st.session_state.show_character_form:
            # Character is ready, show start button
            char = st.session_state.current_character
            st.markdown("### 🎭 Character Ready!")

            col_char1, col_char2 = st.columns([2, 1])
            with col_char1:
                st.markdown(f"**Name:** {char.name}")
                st.markdown(f"**World:** {WORLDS[char.world]}")
                st.markdown(f"**Background:** {char.background}")
                if char.traits:
                    st.markdown(f"**Traits:** {', '.join(char.traits)}")
                st.markdown(f"**Goals:** {char.goals}")

            with col_char2:
                if st.button("🌟 Start Adventure!", type="primary", use_container_width=True):
                    if api_ready:
                        start_new_story(char)
                    else:
                        st.error("❌ Please configure your API in the sidebar first!")

                if st.button("✏️ Edit Character", use_container_width=True):
                    st.session_state.show_character_form = True
                    st.rerun()
        else:
            if st.session_state.show_character_form:
                st.markdown("### 🎭 Create Your Character")
                st.info("👈 Fill out the character form in the sidebar to begin!")
            else:
                display_paginated_story()

    with col2:
        # Tips and info
        st.markdown("### 💡 Tips")
        if not st.session_state.story_started:
            if not st.session_state.current_character:
                st.markdown("""
                **Creating Your Character:**
                - 📝 **Be descriptive** in your background
                - 🎯 **Choose meaningful goals**
                - 🎭 **Experiment** with traits
                - 🌍 **Pick an exciting world**
                """)
            else:
                st.markdown("""
                **Ready to Adventure:**
                - 🌟 **Click "Start Adventure"**
                - ✏️ **Edit character** if needed
                - 🎲 **Try different worlds**
                """)
        else:
            st.markdown("""
            **During Your Adventure:**
            - 🤔 **Think carefully** about choices
            - 🎲 **Experiment** with decisions
            - 📄 **Use pagination** for easy reading
            - 💾 **Stories auto-save** (registered users)
            """)

        # Progress display
        if st.session_state.story_started and st.session_state.story_history:
            st.markdown("### 📈 Your Journey")
            progress = len(st.session_state.story_history.story_chunks)
            st.metric("Chapters Completed", progress)

            total_words = sum(len(chunk.text.split()) for chunk in st.session_state.story_history.story_chunks)
            st.metric("Words Written", f"{total_words:,}")

            # Page info
            if st.session_state.story_history.story_chunks:
                total_pages = (progress - 1) // st.session_state.chapters_per_page + 1
                st.metric("Total Pages", total_pages)

        # Account benefits for guests
        if st.session_state.user_data and st.session_state.user_data.get("user_id") == "guest":
            st.markdown("### 🔓 Upgrade Benefits")
            st.info("""
            **Create an account to:**
            - 💾 Save your stories
            - 📚 Access story library
            - 🔄 Continue adventures later
            - 📱 Sync across devices
            """)

            if st.button("📝 Create Account", type="secondary"):
                st.session_state.authenticated = False
                st.session_state.show_auth_form = "register"
                st.rerun()

if __name__ == "__main__":

    main()

