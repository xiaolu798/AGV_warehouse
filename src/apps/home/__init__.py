from .views.views import route as main_route
from fastapi import APIRouter

home_route = APIRouter()
home_route.include_router(main_route, prefix='/main', tags=["首页核心接口"])
