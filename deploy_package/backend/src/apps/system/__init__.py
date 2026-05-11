from .views.user import router as user_router
from .views.auth import router as auth_route
from .views.job import router as job_route
from .views.dept import router as dept_route
from .views.menu import router as menu_route
from .views.mission import router as mission_route
from fastapi import APIRouter
system_router = APIRouter()
system_router.include_router(user_router, prefix='/user', tags=['用户相关'])
system_router.include_router(auth_route, prefix='/auth', tags=['权限相关'])
system_router.include_router(dept_route, prefix='/dept', tags=['部门相关'])
system_router.include_router(job_route, prefix='/job', tags=['岗位相关'])
system_router.include_router(menu_route, prefix='/menu', tags=['岗位相关'])
system_router.include_router(mission_route, tags=['任务调度'])

