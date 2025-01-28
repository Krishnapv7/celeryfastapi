from celery import Celery
from database import database
from models import AccessLog,ReviewHistory
import openai

celery_app = Celery("tasks",broker="redis://localhost:6379/0")

@celery_app.task
async def log_access_log(log_text:str):
    query = AccessLog.insert().values(text=log_text)
    await database.execute(query)
    
@celery_app.task
async def update_tone_and_sentiment(review_id: int):
    query = ReviewHistory.select().where(ReviewHistory.c.id == review_id)
    review = await database.fetch_one(query)
    
    if review:
        prompt = f"Review: {review['text']}\nStars: {review['stars']}\nProvide tone and sentiment:"
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            max_tokens=50,
        )
        result = response.choices[0].text.strip()
        tone, sentiment = result.split(";") if ";" in result else ("Neutral","Neutral")
        
        update_query = ReviewHistory.update().where(
            ReviewHistory.c.id == review_id
        ).values(tone=tone.strip(),sentiment=sentiment.strip())
        await database.execute(update_query)