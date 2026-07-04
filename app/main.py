from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import whatsapp, auth, invoices, contacts, reports, products, products

app = FastAPI(title="FinanceOS API", version="0.1.0",
              description="Pakistan-first finance platform")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,     prefix="/api/auth",     tags=["auth"])
app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["whatsapp"])
app.include_router(invoices.router, prefix="/api/invoices", tags=["invoices"])
app.include_router(contacts.router, prefix="/api/contacts", tags=["contacts"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(products.router, prefix="/api/products", tags=["products"])

@app.get("/")
def root(): return {"status": "ok", "app": "FinanceOS", "version": "0.1.0"}

@app.get("/health")
def health(): return {"status": "healthy"}
