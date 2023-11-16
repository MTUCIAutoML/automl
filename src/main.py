import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from settings import settings
from routers import router

app = FastAPI(debug=settings.SERVER_TEST)
app.include_router(router)

origins = [
    "localhost:3000",
    "127.0.0.1:3000",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://172.16.1.10:3000"

]

app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],
                   )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.SERVER_ADDR,
        port=settings.SERVER_PORT,
        reload=settings.SERVER_TEST,
        log_level="debug" if settings.SERVER_TEST else "info",
    )
