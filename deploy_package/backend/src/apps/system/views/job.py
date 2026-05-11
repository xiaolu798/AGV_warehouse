from fastapi import APIRouter, Depends
from src.apps.system.models import *
from src.apps.system.schwmas import *
from src.apps.system.views.user import access_token
from src.utils.common_response import APIResponse

router = APIRouter()


# 查询岗位
@router.get('/jobs', description='查询所有岗位')
async def get_jobs(user: User = Depends(access_token)):
    job_data = await Job.filter(is_delete=False).all()
    job_detail = [JobSchemas.model_validate(job).model_dump() for job in job_data]
    return APIResponse(
        msg='岗位查询成功',
        result=job_detail
    )


# 新增岗位
@router.post('/jobs', description='新增岗位')
async def add_job(jobs: JobSchemas,
                  user: User = Depends(access_token)):
    job_data = await Job.create(**jobs.model_dump())
    if job_data:
        return APIResponse(msg='新增岗位成功')
    else:
        raise Exception('岗位新增失败')


# 删除岗位
@router.delete('/jobs', description='删除岗位')
async def delete_job(jobs_ids: list[int],
                     user: User = Depends(access_token)):
    affected_rows = await Job.filter(id__in=jobs_ids).update(is_delete=True)
    if affected_rows > 0:
        return APIResponse(msg=f'成功删除 {affected_rows} 个岗位')
    return APIResponse(code=400, msg='未找到可删除的岗位')


@router.put('/jobs', description='更新一个岗位')
async def update_job(job_id: int,
                     jobs:JobSchemas,
                     user: User = Depends(access_token)
                     ):
    job_data = await Job.filter(id=job_id).update(**jobs.model_dump())
    return APIResponse(msg='修改岗位成功')
