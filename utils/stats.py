import logging
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class Stats:
    """Class for tracking application statistics"""
    tweets_processed: int = 0
    tweets_relevant: int = 0
    tweets_sent: int = 0
    news_processed: int = 0
    news_relevant: int = 0
    news_sent: int = 0
    last_tweet_check: datetime = None
    last_news_check: datetime = None
    processed_tweet_ids: set = field(default_factory=set)
    processed_news_ids: set = field(default_factory=set)
    
    def reset(self):
        """Reset all counters but keep processed IDs"""
        self.tweets_processed = 0
        self.tweets_relevant = 0
        self.tweets_sent = 0
        self.news_processed = 0
        self.news_relevant = 0
        self.news_sent = 0
        self.last_tweet_check = None
        self.last_news_check = None
        # Don't reset processed IDs

# Create a global stats instance
stats = Stats()
