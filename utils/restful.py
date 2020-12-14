from fastapi import FastAPI
from pydantic import BaseModel
import settings

fastapi_app = FastAPI()
stock_status = {}
class Item(BaseModel):
    link: dict
    store: dict

class ResetTarget(BaseModel):
    store: str
    series: str

@fastapi_app.post(settings.restful_endpoint)
async def trigger_event(item: Item):
    series = (item.link['series'])
    store = (item.store['name'])
    if store in stock_status:
        stock_status[store][series] = True
    else:
        stock_status[store] = {series: True}

@fastapi_app.get(settings.restful_endpoint)
async def get_stock_status():
    return stock_status

@fastapi_app.post(settings.restful_endpoint + '/reset')
async def reset_stock_status(target: ResetTarget):
    print(target)
    if target.store in stock_status:
        if target.series in stock_status[target.store]:
            stock_status[target.store][target.series] = False
