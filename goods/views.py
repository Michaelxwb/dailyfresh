from django.shortcuts import render
from django.views.generic import View
from goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from django.core.cache import cache
from django_redis import get_redis_connection


# Create your views here.

# http://127.0.0.1:8000
# class IndexView(View):
#     '''首页'''
#
#     def get(self, request):
#         '''显示首页'''
#         # 尝试从缓存中获取数据
#         context = cache.get('index_page_data')
#
#         if context is None:
#             print('设置缓存')
#             # 缓存中没有数据
#             # 获取商品的种类信息
#             types = GoodsType.objects.all()
#
#             # 获取首页轮播商品信息
#             goods_banners = IndexGoodsBanner.objects.all().order_by('index')
#
#             # 获取首页促销活动信息
#             promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
#
#             # 获取首页分类商品展示信息
#             for type in types:  # GoodsType
#                 # 获取type种类首页分类商品的图片展示信息
#                 image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
#                 # 获取type种类首页分类商品的文字展示信息
#                 title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
#
#                 # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
#                 type.image_banners = image_banners
#                 type.title_banners = title_banners
#
#             context = {'types': types,
#                        'goods_banners': goods_banners,
#                        'promotion_banners': promotion_banners}
#             # 设置缓存
#             # key  value timeout
#             cache.set('index_page_data', context, 3600)
#
#         # 获取用户购物车中商品的数目
#         user = request.user
#         cart_count = 0
#         if user.is_authenticated():
#             # 用户已登录
#             conn = get_redis_connection('default')
#             cart_key = 'cart_%d' % user.id
#             cart_count = conn.hlen(cart_key)
#
#         # 组织模板上下文
#         context.update(cart_count=cart_count)
#
#         # 使用模板
#         return render(request, 'goods/index.html', context)
class IndexView(View):
    def get(self, request):
        '''显示首页'''
        # 尝试从缓存中获取数据
        context = cache.get('index_page_data')

        if context is None:
            print('设置缓存')
            # 获取商品种类信息
            types = GoodsType.objects.all()

            # 获取首页轮播商品信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')

            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')

            # 获取首页分类商品展示信息
            for type in types:  # GoodsType
                # 获取type种类首页分类商品的图片展示信息
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                # 获取type种类首页分类商品的文字展示信息
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')

                # 动态给type增加属性，分别保存首页分类商品的图片展示信息和文字展示信息
                type.image_banners = image_banners
                type.title_banners = title_banners

            # 组织模板上下文
            context = {
                'types': types,
                'goods_banners': goods_banners,
                'promotion_banners': promotion_banners,
            }
            # 设置缓存
            cache.set('index_page_data', context, 3600)

        # 获取用户购物车中商品的数目
        cart_count = 0
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        context.update(cart_count=cart_count)

        # 使用模板渲染页面
        return render(request, 'goods/index.html', context)
