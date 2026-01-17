"""
Twitter Client Module
====================
This module handles Twitter/X API integration using Tweepy.
Provides functions to publish posts to Twitter.
"""

import tweepy
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TwitterClient:
    """
    Handles Twitter/X API operations using Tweepy.
    """
    
    def __init__(self):
        """
        Initialize Twitter client with API credentials from environment.
        """
        # Get Twitter API credentials from environment variables
        api_key = os.getenv("TWITTER_API_KEY")
        api_secret = os.getenv("TWITTER_API_SECRET")
        access_token = os.getenv("TWITTER_ACCESS_TOKEN")
        access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        
        # Validate that all required credentials are present
        if not all([api_key, api_secret, access_token, access_token_secret]):
            raise ValueError(
                "Missing Twitter API credentials. Please check your .env file.\n"
                "Required: TWITTER_API_KEY, TWITTER_API_SECRET, "
                "TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET"
            )
        
        # Initialize Tweepy OAuth1UserHandler for user authentication
        # OAuth1 is used for posting tweets on behalf of a user
        auth = tweepy.OAuth1UserHandler(
            api_key,
            api_secret,
            access_token,
            access_token_secret
        )
        
        # Create API client with authentication
        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Verify credentials by getting user info
        try:
            self.user = self.api.verify_credentials()
            print(f"✓ Successfully authenticated as: @{self.user.screen_name}")
        except Exception as e:
            raise Exception(f"Failed to authenticate with Twitter: {str(e)}")
    
    def publish_post(self, post_text: str) -> dict:
        """
        Publish a post to Twitter/X.
        
        Args:
            post_text: The text content of the post to publish
            
        Returns:
            Dictionary with status information including tweet ID and URL
        """
        try:
            # Check if post is too long (Twitter limit is 280 characters)
            if len(post_text) > 280:
                raise ValueError(
                    f"Post is too long ({len(post_text)} characters). "
                    "Twitter limit is 280 characters."
                )
            
            # Post the tweet using Tweepy
            tweet = self.api.update_status(status=post_text)
            
            # Construct tweet URL
            tweet_url = f"https://twitter.com/{self.user.screen_name}/status/{tweet.id}"
            
            return {
                "success": True,
                "tweet_id": tweet.id,
                "tweet_url": tweet_url,
                "text": post_text,
                "message": f"Post published successfully! View at: {tweet_url}"
            }
            
        except tweepy.TooManyRequests:
            return {
                "success": False,
                "error": "Rate limit exceeded. Please wait before posting again."
            }
        except tweepy.Unauthorized:
            return {
                "success": False,
                "error": "Unauthorized. Please check your Twitter API credentials."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to publish post: {str(e)}"
            }
    
    def test_connection(self) -> bool:
        """
        Test the Twitter API connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.api.verify_credentials()
            return True
        except Exception as e:
            print(f"Connection test failed: {str(e)}")
            return False

