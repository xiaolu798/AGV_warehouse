from tortoise import models, fields

"""搞一个通用表，所有的表可能需要这些字段直接继承"""


class BaseModel(models.Model):
    create_time = fields.DatetimeField(auto_now_add=True, description='创建时间', null=True)
    update_time = fields.DatetimeField(auto_now_add=True, description='更新找时间', null=True)
    create_by = fields.CharField(max_length=32, description='创建者', null=True)
    update_by = fields.CharField(max_length=32, description='更新着', null=True)
    is_delete = fields.BooleanField(default=False, description='是否删除')

    class Meta:
        abstract = True
