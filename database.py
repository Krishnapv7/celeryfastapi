from sqlalchemy import create_engine,MetaData
from databases import Database

DATABASE_URL = "postgresql://krish:mypassword@localhost/assignmentdb"

database = Database(DATABASE_URL)
metadata = MetaData()
engine = create_engine(DATABASE_URL)
metadata.create_all(engine)