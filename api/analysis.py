import logging
import json
import aiohttp
from datetime import datetime

logger = logging.getLogger(__name__)

class AnalysisAPI:
    def __init__(self, api_key, base_url="https://api.x.ai/v1"):
        self.api_key = api_key
        self.base_url = base_url
        
    async def analyze_text(self, text):
        """
        Analyze text using AI API to determine sentiment, relevance, 
        entities and generate a commentary.
        
        Args:
            text: The text to analyze
            
        Returns:
            Dictionary with analysis results or None if error
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for analysis")
            return None
            
        try:
            # Create system prompt to analyze financial text
            system_prompt = """
            You are a financial analyst assistant. Analyze the following financial news or tweet:
            1. Determine if it's relevant to financial markets (crypto, stocks, forex, etc.)
            2. Identify the sentiment (positive, negative, or neutral)
            3. Extract key entities (companies, cryptocurrencies, people, etc.)
            4. Provide a very brief commentary (max 2 sentences) on potential market impact
            5. Assign a confidence score from 0.0 to 1.0

            Respond in JSON format with these fields:
            {
                "relevant": true/false,
                "sentiment": "positive/negative/neutral",
                "entities": ["entity1", "entity2", ...],
                "commentary": "Brief market analysis comment",
                "confidence": 0.XX
            }
            """
            
            # User prompt is the text to analyze
            user_prompt = text
            
            # Prepare request to API
            # Try to adapt to different API structures (either ChatGPT/GPT-4 or similar API format)
            endpoint = f"{self.base_url}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Try adaptive approach for different AI models
            data = {
                # Try alternate model name options
                "model": "gpt-4",  # Default to GPT-4 if available
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.2
            }
            
            start_time = datetime.now()
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=data) as response:
                    response_time = (datetime.now() - start_time).total_seconds()
                    logger.debug(f"AI API response time: {response_time:.2f}s")
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"AI API error ({response.status}): {error_text}")
                        
                        # If model not found, try alternative model
                        if "model not found" in error_text.lower() or "invalid model" in error_text.lower():
                            logger.info("Trying alternative model...")
                            # Try with a more generic model name
                            data["model"] = "gpt-3.5-turbo"  # Fall back to GPT-3.5 if GPT-4 not available
                            
                            # Try again with new model
                            start_time = datetime.now()
                            async with session.post(endpoint, headers=headers, json=data) as retry_response:
                                response_time = (datetime.now() - start_time).total_seconds()
                                logger.debug(f"AI API retry response time: {response_time:.2f}s")
                                
                                if retry_response.status != 200:
                                    retry_error = await retry_response.text()
                                    logger.error(f"AI API retry error ({retry_response.status}): {retry_error}")
                                    return self._create_default_analysis(text)
                                    
                                result = await retry_response.json()
                        else:
                            return self._create_default_analysis(text)
                    else:
                        result = await response.json()
                    
            # Extract content from the AI response
            try:
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                analysis = json.loads(content)
                
                # Ensure all expected fields are present
                analysis.setdefault("relevant", True)  # Default to relevant to prevent missing items
                analysis.setdefault("sentiment", "neutral")
                analysis.setdefault("entities", [])
                analysis.setdefault("commentary", "No commentary available")
                analysis.setdefault("confidence", 0.5)
                
                logger.info(f"Analysis complete. Relevant: {analysis['relevant']}, Sentiment: {analysis['sentiment']}")
                return analysis
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                logger.error(f"Error parsing AI response: {e}")
                logger.debug(f"Raw response: {result}")
                return self._create_default_analysis(text)
                
        except Exception as e:
            logger.error(f"AI API request error: {e}")
            return self._create_default_analysis(text)
            
    def _create_default_analysis(self, text):
        """Create a default analysis when API fails"""
        logger.warning("Using default analysis due to API failure")
        return {
            "relevant": True,
            "sentiment": "neutral",
            "entities": [],
            "commentary": "Analysis currently unavailable. This news may impact markets; please review the details carefully.",
            "confidence": 0.5
        }
