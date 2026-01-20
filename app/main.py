from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, inventory, pos, products, orders, cart,pricing,customer
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-Commerce API")

# -----------------------------
origins = [
    "http://localhost:5173",  # your React dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # list of allowed origins
    allow_credentials=True,
    allow_methods=["*"],         # allow GET, POST, PUT, DELETE...
    allow_headers=["*"],         # allow all headers
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.include_router(inventory.router)
app.include_router(pos.router)
app.include_router(pricing.router)
app.include_router(customer.router)
