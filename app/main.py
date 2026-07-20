from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.ingestion import router as ingestion_router
from app.api.extraction import router as extraction_router
from app.api.clustering import router as clustering_router
from app.api.scoring import router as scoring_router
from app.api.report import router as report_router
from app.api.qa import router as qa_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DiscoveryOS")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingestion_router)
app.include_router(extraction_router)
app.include_router(clustering_router)
app.include_router(scoring_router)
app.include_router(report_router)
app.include_router(qa_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
