from django.contrib import admin

from goods.models import *


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''新增或更新表中的数据时调用'''
        super().save_model(request, obj, form, change)

        # 发出任务 让celery帮我们重新生成静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

    def delete_model(self, request, obj):
        '''删除表中的数据时调用'''
        super().save_model(request, obj)

        # 发出任务 让celery帮我们重新生成静态页面
        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass


class IndexPromotionBannerAdmin(BaseModelAdmin):
    list_display = ['id', 'name', 'url', 'image']


class GoodsSKUAdmin(BaseModelAdmin):
    list_display = ['id', 'name', 'desc', 'price', 'create_time', 'unite', 'image']


admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(Goods)
admin.site.register(GoodsSKU,GoodsSKUAdmin)
admin.site.register(GoodsImage)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
