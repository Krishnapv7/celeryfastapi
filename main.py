from fastapi import FastAPI,Query
from sqlalchemy import select,func,desc,join
from database import database,engine,metadata
from models import ReviewHistory,Category,AccessLog
from tasks import log_access_log,update_tone_and_sentiment

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()
    metadata.create_all(engine)
    
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    
@app.get("/reviews/trends")
async def get_review_trends():
    subquery = select(
        ReviewHistory.c.review_id,
        func.max(ReviewHistory.c.id).label("latest_id")
    ).group_by(ReviewHistory.c.review_id).alias("latest_reviews")
    
    join_condition = ReviewHistory.c.id == subquery.c.latest_id
    query = (
        select(
            Category.c.id,
            Category.c.name,
            Category.c.description,
            func.avg(ReviewHistory.c.stars).label("average_stars"),
            func.count(ReviewHistory.c.id).label("total_reviews")
        )
        .select_from(
            join(ReviewHistory,subquery,join_condition).join(
                Category,ReviewHistory.c.category_id == Category.c.id
            )
        )
        .group_by(Category.c.id)
        .order_by(desc(func.avg(ReviewHistory.c.stars)))
        .limit(5)
    )        
    
    result = await database.fetch_all(query)
    
    log_access_log.delay("GET /reviews/trends")
    return [
        {
            "id":row["id"],
            "name":row["name"],
            "description":row["description"],
            "average_stars":row["average_stars"],
            "total_reviews":row["total_reviews"],
        }
        for row in result
    ]
    

@app.get("/reviews/")
async def get_reviews(category_id: int,page: int=1):
    page_size = 15
    offset = (page - 1) * 15
    
    subquery = select(
        ReviewHistory.c.review_id,
        func.max(ReviewHistory.c.id).label("latest_id")
    ).group_by(ReviewHistory.c.review_id).alias("latest_reviews")
    
    join_condition = ReviewHistory.c.id == subquery.c.latest_id
    query = (
        select(
            ReviewHistory.c.id,
            ReviewHistory.c.text,
            ReviewHistory.c.stars,
            ReviewHistory.c.review_id,
            ReviewHistory.c.created_at,
            ReviewHistory.c.tone,
            ReviewHistory.c.sentiment,
            ReviewHistory.c.category_id,
        )
        .select_from(
            join(ReviewHistory,subquery,join_condition)
        )
        .where(ReviewHistory.c.category_id == category_id)
        .order_by(desc(ReviewHistory.c.created_at))
        .offset(offset)
        .limit(page_size)
    )
    
    reviews = await database.fetch_all(query)
    
    log_access_log.delay(f"GET /reviews/?category_id={category_id}")
    
    for review in reviews:
        if not review["tone"] or not review["sentiment"]:
            update_tone_and_sentiment.delay(review["id"])
    return reviews
    