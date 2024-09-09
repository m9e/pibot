from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
import os
import sys
from openai import AzureOpenAI

class LLMConfig(BaseModel):
    """Configuration for the LLM class."""
    model: str
    api_type: str = "azure"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    deployment_name: Optional[str] = None

class LLM:
    """A class to interact with Azure OpenAI models."""

    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM class.

        Args:
            config (LLMConfig): The configuration for the LLM.
        """
        self.config = config
        self.client = self._initialize_client()

    def _initialize_client(self) -> Any:
        """Initialize the Azure OpenAI client based on the configuration."""
        return AzureOpenAI(
            api_key=self.config.api_key,
            api_version=self.config.api_version,
            azure_endpoint=self.config.api_base
        )

    def generate(self, messages: List[Dict[str, str]], 
                limit: Optional[int] = None, temperature: Optional[float] = None) -> str:
        """
        Generate a response using the configured LLM.
        Args:
            messages (List[Dict[str, str]]): List of message dictionaries with 'role' and 'content'.
            limit (Optional[int]): The maximum number of tokens to generate.
            temperature (Optional[float]): The sampling temperature to use.
        Returns:
            str: The response from the LLM.
        """
        try:
            kwargs = {
                "messages": messages,
                "temperature": temperature if temperature is not None else 0.7,
                "model": self.config.deployment_name,
            }
            if limit is not None:
                kwargs["max_tokens"] = limit
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error calling API: {e}", file=sys.stderr)
            raise e

def load_api_keys():
    """Load API keys from ~/.api_keys file."""
    api_keys_path = os.path.expanduser("~/.api_keys")
    if os.path.exists(api_keys_path):
        with open(api_keys_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value.strip('"').strip("'")

def main():
    # Load API keys
    load_api_keys()

    # Azure OpenAI configuration
    azure_config = LLMConfig(
        model="gpt-4",  # This is not used directly in the API call
        api_type="azure",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        api_version="2023-05-15"
    )

    # Create LLM instance
    azure_llm = LLM(azure_config)

    # Test prompt
    prompt = "Explain the concept of recursion in programming using a simple analogy."

    print("Sending request to Azure OpenAI...")
    try:
        response = azure_llm.generate(prompt)
        print("\nAzure OpenAI response:")
        print(response)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

    print("\nAzure OpenAI call completed successfully!")

if __name__ == "__main__":
    main()