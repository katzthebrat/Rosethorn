import asyncio
import aiohttp
import json
from datetime import datetime
import config
import logging

logger = logging.getLogger(__name__)

class AIService:
    """AI service for content generation, moderation, and assistance"""
    
    def __init__(self):
        self.session = None
        self.personality = {
            'style': 'gothic_victorian',
            'tone': 'elegant_formal',
            'vocabulary': 'sophisticated',
            'theme': 'romantic_gothic'
        }
    
    async def get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate_response(self, prompt, context=None, max_tokens=150):
        """Generate AI response using OpenAI API"""
        if not config.OPENAI_API_KEY:
            return None
        
        try:
            session = await self.get_session()
            
            # Build system message with Gothic Victorian personality
            system_message = self._build_system_message()
            
            messages = [
                {"role": "system", "content": system_message}
            ]
            
            if context:
                messages.append({"role": "user", "content": f"Context: {context}"})
            
            messages.append({"role": "user", "content": prompt})
            
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                'Authorization': f'Bearer {config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': 'gpt-3.5-turbo',
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': 0.8,
                'presence_penalty': 0.1,
                'frequency_penalty': 0.1
            }
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content'].strip()
                else:
                    error_text = await response.text()
                    logger.error(f"OpenAI API error {response.status}: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return None
    
    def _build_system_message(self):
        """Build system message for AI personality"""
        return """You are RosethornBot, an elegant AI assistant for a Gothic Victorian Discord server. 
        
        Personality traits:
        - Speak with Victorian elegance and Gothic romance
        - Use sophisticated vocabulary and formal address ("thou", "thy", "thee")
        - Reference roses, thorns, candlelight, manor halls, and Gothic aesthetics
        - Maintain a mysterious yet welcoming tone
        - Be helpful while staying in character
        - Use emojis sparingly: 🌹 🕯️ 🌙 ⭐ 👑 💎
        
        Always respond as if you are the guardian spirit of a beautiful Gothic manor, welcoming guests with Victorian grace."""
    
    async def moderate_content(self, text):
        """AI-powered content moderation"""
        if not config.OPENAI_API_KEY:
            return {'safe': True, 'categories': [], 'confidence': 0}
        
        try:
            session = await self.get_session()
            
            url = "https://api.openai.com/v1/moderations"
            headers = {
                'Authorization': f'Bearer {config.OPENAI_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            data = {'input': text}
            
            async with session.post(url, headers=headers, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    moderation = result['results'][0]
                    
                    flagged_categories = []
                    for category, flagged in moderation['categories'].items():
                        if flagged:
                            flagged_categories.append(category)
                    
                    return {
                        'safe': not moderation['flagged'],
                        'categories': flagged_categories,
                        'confidence': max(moderation['category_scores'].values()) if moderation['category_scores'] else 0
                    }
                else:
                    logger.error(f"Moderation API error: {response.status}")
                    return {'safe': True, 'categories': [], 'confidence': 0}
                    
        except Exception as e:
            logger.error(f"Error in content moderation: {e}")
            return {'safe': True, 'categories': [], 'confidence': 0}
    
    async def analyze_sentiment(self, text):
        """Analyze sentiment of text"""
        prompt = f"Analyze the sentiment of this message and respond with just one word: positive, negative, or neutral.\n\nMessage: {text}"
        
        response = await self.generate_response(prompt, max_tokens=10)
        
        if response:
            sentiment = response.lower().strip()
            if sentiment in ['positive', 'negative', 'neutral']:
                return sentiment
        
        return 'neutral'
    
    async def generate_welcome_message(self, username, guild_name):
        """Generate personalized welcome message"""
        prompt = f"Generate a Gothic Victorian welcome message for a new member named {username} joining the Discord server '{guild_name}'. Keep it elegant and welcoming."
        
        response = await self.generate_response(prompt, max_tokens=100)
        
        if response:
            return response
        
        # Fallback message
        return f"Welcome to our Gothic manor, {username}! May thy journey here be filled with Victorian elegance and Gothic wonder. 🌹"
    
    async def generate_embed_content(self, topic, style='informative'):
        """Generate content for Discord embeds"""
        style_prompts = {
            'informative': f"Create informative content about {topic} in Gothic Victorian style",
            'announcement': f"Create an elegant announcement about {topic} for a Gothic Discord server",
            'celebration': f"Create a celebratory message about {topic} with Gothic Victorian flair",
            'mysterious': f"Create mysterious, intriguing content about {topic} in Gothic style"
        }
        
        prompt = style_prompts.get(style, style_prompts['informative'])
        
        response = await self.generate_response(prompt, max_tokens=200)
        
        return response or f"Content about {topic} - generated with Gothic elegance."
    
    async def suggest_custom_commands(self, guild_activity):
        """Suggest custom commands based on guild activity"""
        prompt = f"Based on this Discord server activity: {guild_activity}, suggest 3 useful custom commands for a Gothic Victorian themed bot. Be creative and helpful."
        
        response = await self.generate_response(prompt, max_tokens=150)
        
        if response:
            return response
        
        return "Consider adding commands for Gothic quotes, manor rules, or elegant announcements."
    
    async def generate_ticket_response(self, ticket_content):
        """Generate helpful response for ticket content"""
        prompt = f"A user has created a support ticket with this content: '{ticket_content}'. Generate a helpful, empathetic first response from a Gothic Victorian bot."
        
        response = await self.generate_response(prompt, max_tokens=120)
        
        return response or "Thank thee for thy request. Our Gothic staff shall assist thee shortly with Victorian grace."
    
    async def analyze_application(self, application_data):
        """Analyze application responses and provide insights"""
        prompt = f"Analyze this job application data and provide a brief assessment: {application_data}. Focus on helpfulness and professionalism."
        
        response = await self.generate_response(prompt, max_tokens=100)
        
        return response or "Application shows potential and dedication to our Gothic community."
    
    async def generate_social_post_summary(self, posts):
        """Generate summary of social media posts"""
        if not posts:
            return "No recent social media activity to summarize."
        
        post_text = " | ".join([post.get('content', post.get('title', ''))[:50] for post in posts])
        prompt = f"Summarize these recent social media posts in Gothic Victorian style: {post_text}"
        
        response = await self.generate_response(prompt, max_tokens=80)
        
        return response or "Recent social media activity has graced our digital presence."
    
    async def improve_message(self, original_message, improvement_type='clarity'):
        """Improve a message for clarity, style, or tone"""
        improvement_prompts = {
            'clarity': f"Improve this message for clarity while maintaining Gothic Victorian style: {original_message}",
            'style': f"Rewrite this message with more Gothic Victorian elegance: {original_message}",
            'tone': f"Adjust the tone of this message to be more welcoming and Gothic: {original_message}",
            'formal': f"Make this message more formal and Victorian: {original_message}"
        }
        
        prompt = improvement_prompts.get(improvement_type, improvement_prompts['clarity'])
        
        response = await self.generate_response(prompt, max_tokens=150)
        
        return response or original_message
    
    async def detect_language(self, text):
        """Detect language of text"""
        prompt = f"What language is this text written in? Respond with just the language name.\n\nText: {text[:100]}"
        
        response = await self.generate_response(prompt, max_tokens=10)
        
        if response:
            return response.strip().lower()
        
        return 'english'
    
    async def generate_server_insights(self, server_stats):
        """Generate insights about server activity"""
        prompt = f"Analyze these Discord server statistics and provide helpful insights: {server_stats}. Focus on community growth and engagement."
        
        response = await self.generate_response(prompt, max_tokens=120)
        
        return response or "Thy Gothic community shows signs of healthy growth and engagement."
    
    async def create_personalized_content(self, user_preferences, content_type):
        """Create personalized content based on user preferences"""
        prompt = f"Create {content_type} content for a user with these preferences: {user_preferences}. Use Gothic Victorian style."
        
        response = await self.generate_response(prompt, max_tokens=100)
        
        return response or f"Personalized {content_type} created with Gothic elegance."
    
    async def validate_api_key(self):
        """Validate OpenAI API key"""
        if not config.OPENAI_API_KEY:
            return False
        
        try:
            # Test with a simple request
            test_response = await self.generate_response("Hello", max_tokens=5)
            return test_response is not None
        except Exception as e:
            logger.error(f"Error validating OpenAI API key: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
