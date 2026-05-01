from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routes import auth_routes, data_routes, history_routes

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="空气质量数据分析平台 API",
    description="一个基于 FastAPI 的空气质量数据分析平台，支持数据上传、清洗、可视化和历史记录管理",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/api")
app.include_router(data_routes.router, prefix="/api")
app.include_router(history_routes.router, prefix="/api")

@app.get("/")
def root():
    return {
        "message": "空气质量数据分析平台 API 运行中",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
