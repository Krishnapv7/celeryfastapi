from celery import Celery
from database import database
from models import AccessLog,ReviewHistory
import asyncio
import openai
openai.api_key = "api-key"

celery_app = Celery("tasks",broker="redis://localhost:6379/0")

@celery_app.task
def log_access_log(log_text: str):
    async def _log_access_log():
        await database.connect()
        query = AccessLog.insert().values(text=log_text)
        await database.execute(query)
        await database.disconnect()
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_log_access_log())
    
@celery_app.task
def update_tone_and_sentiment(review_id: int):
    async def _update_tone_and_sentiment():
        await database.connect()
        query = ReviewHistory.select().where(ReviewHistory.c.id == review_id)
        review = await database.fetch_one(query)
    
        if review:
            prompt = f"Review: {review['text']}\nStars: {review['stars']}\nProvide tone and sentiment:"
            response = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
            )
            result = response.choices[0].message.content.strip()
            tone, sentiment = result.split(";") if ";" in result else ("Neutral","Neutral")
            
            update_query = ReviewHistory.update().where(
                ReviewHistory.c.id == review_id
            ).values(tone=tone.strip(),sentiment=sentiment.strip())
            await database.execute(update_query)
        await database.disconnect()
        
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_update_tone_and_sentiment())