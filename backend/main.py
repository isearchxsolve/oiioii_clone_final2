from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import health

app = FastAPI(title="oiioii_clone_final2")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(health.router, prefix="/api")
