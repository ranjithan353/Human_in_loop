"""
Post Generator Module
=====================
This module handles the generation of social media posts from news articles.
Uses LangChain with Ollama to create engaging LinkedIn/X posts.
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PostGenerator:
    """
    Generates social media posts from news articles using Ollama (local LLM).
    """
    
    def __init__(self, model_name=None, temperature=0.7, base_url=None):
        """
        Initialize the post generator with Ollama model.
        
        Args:
            model_name: The Ollama model to use (default: llama3.2 or from env)
            temperature: Controls randomness (0.0 = deterministic, 1.0 = creative)
            base_url: Ollama API base URL (default: http://localhost:11434)
        """
        # Get model name from environment or use default
        if model_name is None:
            model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
        
        # Get Ollama base URL from environment or use default
        if base_url is None:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Check if Ollama is running
        try:
            import requests
            response = requests.get(f"{base_url}/api/tags", timeout=2)
            if response.status_code != 200:
                raise ConnectionError(f"Ollama API returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "\n" + "="*60 + "\n"
                "❌ Cannot connect to Ollama!\n\n"
                "Please make sure Ollama is running:\n"
                "1. Install Ollama from: https://ollama.ai\n"
                "2. Start Ollama service\n"
                "3. Pull a model: ollama pull llama3.2\n"
                "4. Verify it's running: ollama list\n\n"
                "Default Ollama URL: http://localhost:11434\n"
                "You can change it in .env: OLLAMA_BASE_URL=your_url\n"
                "="*60 + "\n"
            )
        except Exception as e:
            print(f"⚠️  Warning: Could not verify Ollama connection: {e}")
            print("   Continuing anyway...")
        
        # Initialize the Ollama chat model
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url
        )
        
        # Get post preferences from environment
        self.tone = os.getenv("POST_TONE", "professional")
        self.max_length = int(os.getenv("POST_MAX_LENGTH", "280"))
    
    def generate_post(self, article_text: str) -> str:
        """
        Generate a social media post from a news article.
        
        Args:
            article_text: The full text of the news article
            
        Returns:
            A generated social media post
        """
        # Create a prompt template for post generation
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert social media content creator specializing in LinkedIn and X (Twitter) posts.
            
Your task is to create engaging, professional posts that:
- Capture the key insights from the article
- Are concise and impactful (under {max_length} characters)
- Use a {tone} tone
- Include relevant hashtags (2-3 maximum)
- Encourage engagement
- Are suitable for professional social media platforms

Format your response as a clean post without any additional commentary or explanations."""),
            ("human", "Create a social media post based on this article:\n\n{article}")
        ])
        
        # Format the prompt with article content
        formatted_prompt = prompt.format_messages(
            article=article_text,
            tone=self.tone,
            max_length=self.max_length
        )
        
        # Generate the post using the LLM
        response = self.llm.invoke(formatted_prompt)
        
        # Extract the post text from the response
        post_content = response.content.strip()
        
        return post_content
    
    def regenerate_post(self, article_text: str, feedback: str) -> str:
        """
        Regenerate a post based on user feedback.
        
        Args:
            article_text: The original news article
            feedback: User's feedback/editing instructions
            
        Returns:
            A regenerated social media post
        """
        # Create a prompt that includes feedback
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert social media content creator.
            
Your task is to revise a social media post based on user feedback.
- Follow the feedback instructions carefully
- Maintain a {tone} tone
- Keep it under {max_length} characters
- Include relevant hashtags (2-3 maximum)
- Make it engaging and professional

Format your response as a clean post without any additional commentary."""),
            ("human", """Original article:
{article}

User feedback/editing instructions:
{feedback}

Please regenerate the post based on this feedback.""")
        ])
        
        # Format and generate
        formatted_prompt = prompt.format_messages(
            article=article_text,
            feedback=feedback,
            tone=self.tone,
            max_length=self.max_length
        )
        
        response = self.llm.invoke(formatted_prompt)
        post_content = response.content.strip()
        
        return post_content

