"""
Configuration module for Novel Diver - Interactive Fanfiction MVP

This module handles API key management and client initialization for various AI providers.
It supports multiple AI APIs with fallback options and proper error handling.
"""

import os
import time
import logging
import requests
from typing import Optional, Any, Tuple
import google.generativeai as genai
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    """Configuration class for managing API keys and client initialization."""

    def __init__(self):
        # Initialize with None to force fresh validation
        self.gemini_api_key = None
        self.huggingface_token = None
        self.openai_api_key = None
        self._clients_cache = {}

        # Check environment variables
        self._load_api_keys()

        # Validate available APIs
        self.available_apis = []
        self._validate_all_apis()

    def _load_api_keys(self):
        """Load API keys from environment variables and Streamlit secrets."""
        # Try to get from environment variables first
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # If Streamlit is available, also check secrets
        if STREAMLIT_AVAILABLE:
            try:
                if not self.gemini_api_key:
                    self.gemini_api_key = st.secrets.get("GEMINI_API_KEY")
                if not self.huggingface_token:
                    self.huggingface_token = st.secrets.get("HUGGINGFACE_TOKEN")
                if not self.openai_api_key:
                    self.openai_api_key = st.secrets.get("OPENAI_API_KEY")
            except:
                # Secrets not available or not configured
                pass

    def validate_api_key(self, api_name: str, api_key: str) -> Tuple[bool, str]:
        """
        Validate an API key by making a test request.

        Args:
            api_name: The API to validate ("gemini", "huggingface", "openai")
            api_key: The API key to validate

        Returns:
            tuple: (is_valid, status_message)
        """

        if api_name == "gemini":
            return self._validate_gemini_key(api_key)
        elif api_name == "huggingface":
            return self._validate_huggingface_token(api_key)
        elif api_name == "openai":
            return self._validate_openai_key(api_key)
        else:
            return False, f"Unknown API: {api_name}"

    def _validate_gemini_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate Gemini API key."""
        try:
            # Configure with the new key
            genai.configure(api_key=api_key)

            # Try to create a model and make a test request
            model = genai.GenerativeModel('gemini-1.5-flash')  # Use the latest free model

            # Make a minimal test request
            response = model.generate_content(
                "Hello",
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10,
                    temperature=0.1
                )
            )

            if response and response.text:
                return True, "✅ Gemini API key is valid and working!"
            else:
                return False, "❌ Gemini API returned empty response"

        except Exception as e:
            error_msg = str(e).lower()

            if "api key not valid" in error_msg or "api_key_invalid" in error_msg:
                return False, "❌ Invalid Gemini API key"
            elif "quota" in error_msg or "limit" in error_msg:
                return False, "❌ Gemini API quota exceeded or rate limited"
            elif "403" in error_msg:
                return False, "❌ Gemini API access forbidden - check your API key permissions"
            elif "404" in error_msg:
                return False, "❌ Gemini API endpoint not found - check if the service is available"
            else:
                return False, f"❌ Gemini API error: {str(e)[:100]}"

    def _validate_huggingface_token(self, token: str) -> Tuple[bool, str]:
        """Validate Hugging Face token."""
        try:
            # Test with a simple model endpoint
            headers = {"Authorization": f"Bearer {token}"}

            # Try to get model info (lightweight request)
            response = requests.get(
                "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium",
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                return True, "✅ Hugging Face token is valid!"
            elif response.status_code == 401:
                return False, "❌ Invalid Hugging Face token"
            elif response.status_code == 403:
                return False, "❌ Hugging Face token access forbidden"
            elif response.status_code == 429:
                return False, "❌ Hugging Face rate limit exceeded"
            else:
                return False, f"❌ Hugging Face error: HTTP {response.status_code}"

        except requests.exceptions.Timeout:
            return False, "❌ Hugging Face API timeout - please try again"
        except requests.exceptions.RequestException as e:
            return False, f"❌ Hugging Face connection error: {str(e)[:50]}"
        except Exception as e:
            return False, f"❌ Hugging Face validation error: {str(e)[:50]}"

    def _validate_openai_key(self, api_key: str) -> Tuple[bool, str]:
        """Validate OpenAI API key."""
        try:
            import openai

            # Set the API key
            openai.api_key = api_key

            # Make a test request with minimal tokens
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0
            )

            if response and response.choices:
                return True, "✅ OpenAI API key is valid!"
            else:
                return False, "❌ OpenAI API returned empty response"

        except Exception as e:
            error_msg = str(e).lower()

            if "invalid api key" in error_msg or "incorrect api key" in error_msg:
                return False, "❌ Invalid OpenAI API key"
            elif "quota" in error_msg or "billing" in error_msg:
                return False, "❌ OpenAI quota exceeded or billing issue"
            elif "rate limit" in error_msg:
                return False, "❌ OpenAI rate limit exceeded"
            else:
                return False, f"❌ OpenAI error: {str(e)[:100]}"

    def set_and_validate_api_key(self, api_name: str, api_key: str) -> Tuple[bool, str]:
        """
        Set and validate an API key, updating the configuration if valid.

        Args:
            api_name: The API name
            api_key: The API key to set and validate

        Returns:
            tuple: (is_valid, status_message)
        """
        # Clear any cached clients first
        self._clients_cache.clear()

        # Validate the key
        is_valid, message = self.validate_api_key(api_name, api_key)

        if is_valid:
            # Set the API key
            if api_name == "gemini":
                self.gemini_api_key = api_key
                os.environ["GEMINI_API_KEY"] = api_key
            elif api_name == "huggingface":
                self.huggingface_token = api_key
                os.environ["HUGGINGFACE_TOKEN"] = api_key
            elif api_name == "openai":
                self.openai_api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key

            # Update available APIs
            self._validate_all_apis()

        return is_valid, message

    def _validate_all_apis(self):
        """Check which APIs are available and valid."""
        self.available_apis = []

        if self.gemini_api_key:
            is_valid, _ = self._validate_gemini_key(self.gemini_api_key)
            if is_valid:
                self.available_apis.append("gemini")
                logger.info("Gemini API validated successfully")

        if self.huggingface_token:
            is_valid, _ = self._validate_huggingface_token(self.huggingface_token)
            if is_valid:
                self.available_apis.append("huggingface")
                logger.info("Hugging Face API validated successfully")

        if self.openai_api_key:
            is_valid, _ = self._validate_openai_key(self.openai_api_key)
            if is_valid:
                self.available_apis.append("openai")
                logger.info("OpenAI API validated successfully")

        if not self.available_apis:
            logger.warning("No valid API keys found!")

    def get_llm_client(self, preferred_api: str = "gemini") -> tuple[Any, str]:
        """
        Get an initialized LLM client based on preference and availability.

        Args:
            preferred_api: The preferred API to use ("gemini", "huggingface", "openai")

        Returns:
            tuple: (client_object, api_name) or (None, None) if no APIs available
        """

        # Check cache first
        if preferred_api in self._clients_cache and preferred_api in self.available_apis:
            return self._clients_cache[preferred_api], preferred_api

        # Try preferred API first
        if preferred_api in self.available_apis:
            try:
                client = self._initialize_client(preferred_api)
                self._clients_cache[preferred_api] = client
                return client, preferred_api
            except Exception as e:
                logger.error(f"Failed to initialize {preferred_api}: {e}")

        # Fallback to any available API
        for api in self.available_apis:
            try:
                if api not in self._clients_cache:
                    client = self._initialize_client(api)
                    self._clients_cache[api] = client
                return self._clients_cache[api], api
            except Exception as e:
                logger.error(f"Failed to initialize {api}: {e}")
                continue

        logger.error("No working API clients available")
        return None, None

    def _initialize_client(self, api_name: str) -> Any:
        """Initialize a specific API client."""

        if api_name == "gemini":
            genai.configure(api_key=self.gemini_api_key)
            # Use the latest free Gemini model
            return genai.GenerativeModel('gemini-1.5-flash')

        elif api_name == "huggingface":
            # We'll use requests for Hugging Face API calls
            return {
                "token": self.huggingface_token,
                "api_url": "https://api-inference.huggingface.co/models/",
                "model": "microsoft/DialoGPT-large"  # Good free model for stories
            }

        elif api_name == "openai":
            import openai
            openai.api_key = self.openai_api_key
            return openai

        else:
            raise ValueError(f"Unsupported API: {api_name}")

    def clear_cache(self):
        """Clear the clients cache to force reinitialization."""
        self._clients_cache.clear()

    def refresh_api_keys(self):
        """Refresh API keys from environment and revalidate."""
        self._load_api_keys()
        self.clear_cache()
        self._validate_all_apis()

    def retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """
        Retry a function with exponential backoff for rate limiting.

        Args:
            func: Function to retry
            max_retries: Maximum number of retry attempts
            base_delay: Base delay in seconds

        Returns:
            Function result or raises the last exception
        """

        for attempt in range(max_retries + 1):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries:
                    raise e

                # Check if it's a rate limit error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ["rate limit", "429", "quota", "too many requests"]):
                    delay = base_delay * (2 ** attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay}s... (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(delay)
                else:
                    raise e

# Global configuration instance
config = Config()

def get_client(preferred_api: str = "gemini"):
    """
    Convenience function to get an LLM client.

    Args:
        preferred_api: The preferred API to use

    Returns:
        tuple: (client, api_name) or (None, None) if unavailable
    """
    return config.get_llm_client(preferred_api)

def validate_and_set_api_key(api_name: str, api_key: str) -> Tuple[bool, str]:
    """
    Convenience function to validate and set an API key.

    Args:
        api_name: The API name
        api_key: The API key to validate and set

    Returns:
        tuple: (is_valid, status_message)
    """
    return config.set_and_validate_api_key(api_name, api_key)