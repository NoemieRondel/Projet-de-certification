from fastapi import FastAPI
from app.routes import articles_route, videos_route, scientific_articles_route

app = FastAPI()

# Inclusion des routes
app.include_router(articles_route.router, prefix="/articles", tags=["Articles"])
app.include_router(videos_route.router, prefix="/videos", tags=["Videos"])
app.include_router(scientific_articles_route.router, prefix="/scientific-articles", tags=["Scientific Articles"])


@app.get("/")
async def root():
    return {"message": "Bienvenue sur l'API Veille IA !"}
