from django.db import models
from django.contrib.auth.models import AbstractUser
from db.base_model import BaseModel


# Create your models here.


class User(AbstractUser, BaseModel):
    '''用户模型类'''

    class Meta:
        db_table = 'df_user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username


class AddressManager(models.Manager):
    def get_default_address(self, user):
        try:
            # 存在默认收货地址
            address = super().get(user=user, is_default=True)
        except self.model.DoesNotExist:
            # 不存在默认收货地址
            address = None
        return address


class Address(BaseModel):
    '''地址模型类'''
    user = models.ForeignKey('User', verbose_name='所属账户', on_delete=models.CASCADE)
    receiver = models.CharField(max_length=20, verbose_name='收件人')
    addr = models.CharField(max_length=256, verbose_name='收件地址')
    zip_code = models.CharField(max_length=6, null=True, verbose_name='邮政编码')
    phone = models.CharField(max_length=11, verbose_name='联系电话')
    is_default = models.BooleanField(default=False, verbose_name='是否默认')

    class Meta:
        db_table = 'df_address'
        verbose_name = '地址'
        verbose_name_plural = verbose_name

    # 自定义一个模型管理器类对象
    objects = AddressManager()

    def __str__(self):
        user = User.objects.get(id=self.user_id)
        if not self.is_default:
            user_addr = user.username + '的地址'
        else:
            user_addr = user.username + '的默认地址'
        return user_addr
