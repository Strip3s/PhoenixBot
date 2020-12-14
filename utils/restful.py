from fastapi import FastAPI
from pydantic import BaseModel

fastapi_app = FastAPI()
stock_status = {}
class Item(BaseModel):
    link: dict
    store: dict

@fastapi_app.post('/api/notification')
async def trigger_event(item: Item):
    series = (item.link['series'])
    store = (item.store['name'])
    if store in stock_status:
        stock_status[store][series] = True
    else:
        stock_status[store] = {series: True}

@fastapi_app.get('/api/notification')
async def get_stock_status():
    return stock_status