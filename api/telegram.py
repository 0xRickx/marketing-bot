import os
import logging
import aiohttp
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes
from utils.stats import stats

logger = logging.getLogger(__name__)

class TelegramAPI:
    def __init__(self, bot_token, chat_id, topic_id=None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.topic_id = topic_id
        self.application = None
        
    def build_application(self):
        """Build and configure the Telegram application"""
        self.application = Application.builder().token(self.bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("stats", self.stats_command))
        
        return self.application
    
    async def test_connection(self):
        """Test the Telegram connection by sending a test message"""
        try:
            if not self.application:
                logger.error("Application not initialized")
                return False
                
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=self.topic_id,
                text="🤖 Market Monitor bot started successfully!"
            )
            logger.info("Telegram connection test successful")
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
            
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /stats command"""
        stats_text = (
            "📊 *Market Monitor Statistics*\n\n"
            f"🐦 Tweets processed: {stats.tweets_processed}\n"
            f"🐦 Relevant tweets: {stats.tweets_relevant}\n"
            f"📰 News articles processed: {stats.news_processed}\n"
            f"📰 Relevant news articles: {stats.news_relevant}\n\n"
            f"Last tweet check: {stats.last_tweet_check.strftime('%Y-%m-%d %H:%M:%S UTC') if stats.last_tweet_check else 'Never'}\n"
            f"Last news check: {stats.last_news_check.strftime('%Y-%m-%d %H:%M:%S UTC') if stats.last_news_check else 'Never'}"
        )
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
            
    async def send_tweet_alert(self, screen_name, tweet_text, tweet_id, analysis):
        """Send a Telegram alert for a relevant tweet"""
        if not self.application:
            logger.error("Application not initialized")
            return
            
        tweet_url = f"https://twitter.com/{screen_name}/status/{tweet_id}"
        sentiment = analysis.get('sentiment', 'neutral').capitalize()
        
        # Get emoji based on sentiment
        emoji = {"positive": "🟢", "neutral": "⚪", "negative": "🔴"}.get(sentiment.lower(), "⚪")
        
        message = (
            f"🐦 *Tweet from @{screen_name}*\n\n"
            f"{tweet_text}\n\n"
            f"*Sentiment:* {emoji} {sentiment}\n"
            f"*Confidence:* {analysis.get('confidence', 0):.0%}\n"
            f"*Entities:* {', '.join(analysis.get('entities', ['None']))}"
        )
        
        # Create inline keyboard with tweet URL
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="View Tweet", url=tweet_url)]
        ])
        
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=self.topic_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info(f"Tweet alert sent for {screen_name}")
            stats.tweets_sent += 1
        except Exception as e:
            logger.error(f"Error sending tweet alert: {e}")
    
    async def send_news_alert(self, article, analysis):
        """Send a Telegram alert for a relevant news article with Grok commentary"""
        if not self.application:
            logger.error("Application not initialized")
            return
            
        # Extract required fields
        headline = article.get('headline', 'No headline')
        summary = article.get('summary', 'No summary')
        url = article.get('url', '#')
        source = article.get('source', 'Unknown source')
        
        # Get sentiment analysis
        sentiment = analysis.get('sentiment', 'neutral').lower()
        
        # Determine market sentiment indicator
        if sentiment == 'positive':
            market_indicator = "🟢 BULLISH"
        elif sentiment == 'negative':
            market_indicator = "🔴 BEARISH"
        else:
            market_indicator = "⚪ NEUTRAL"
            
        # Get commentary from analysis
        grok_commentary = analysis.get('commentary', 'No analysis available')
        
        # Create message
        message = (
            f"📰 *{headline}*\n\n"
            f"{summary}\n\n"
            f"*Source:* {source}\n"
            f"*Market Sentiment:* {market_indicator}\n\n"
            f"*Grok Analysis:*\n{grok_commentary}"
        )
        
        # Create inline keyboard with article URL
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(text="Read Article", url=url)]
        ])
        
        try:
            await self.application.bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=self.topic_id,
                text=message,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            logger.info(f"News alert sent: {headline}")
            stats.news_sent += 1
        except Exception as e:
            logger.error(f"Error sending news alert: {e}")
