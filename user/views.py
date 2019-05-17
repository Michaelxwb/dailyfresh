import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import View
from itsdangerous import SignatureExpired
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from utils.mixin import LoginRequireMixin
from redis import *
from django_redis import get_redis_connection

from celery_tasks.tasks import send_register_active_email
from user.models import User, Address
from goods.models import GoodsSKU


# from celery_tasks.tasks import dictURL


# Create your views here.


def register(request):
    '''注册页面'''
    if request.method == "GET":
        # 显示注册页面
        return render(request, 'user/register.html')
    else:
        '''接收注册页面发送过来的数据，并进行处理'''
        # 1.接收用户名，密码，邮箱，是否同意协议
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.对接收到的数据进行校验
        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})

        # 邮箱校验
        if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式错误'})

        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 判断用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在可以注册
            user = None
        if user:
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})
        # 3.进行业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 4.返回响应数据
        return redirect(reverse('goods:index'))


class RegisterView(View):
    def get(self, request):
        # 显示注册页面
        return render(request, 'user/register.html')

    def post(self, request):
        '''接收注册页面发送过来的数据，并进行处理'''
        # 1.接收用户名，密码，邮箱，是否同意协议
        username = request.POST.get('user_name')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 2.对接收到的数据进行校验
        if not all([username, password, email]):
            return render(request, 'user/register.html', {'errmsg': '数据不完整'})

        # 邮箱校验
        if not re.match(r'[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'user/register.html', {'errmsg': '邮箱格式错误'})

        if allow != 'on':
            return render(request, 'user/register.html', {'errmsg': '请同意协议'})

        # 判断用户名是否已注册
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户名不存在可以注册
            user = None
        if user:
            return render(request, 'user/register.html', {'errmsg': '用户名已存在'})
        # 3.进行业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 向用户注册的邮箱中发送激活连接，连接中必须包含唯一识别用户的信息(id或者username),并且这个信息需要加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {"confirm": user.id}

        # 加密用户的身份信息，生成激活token
        token = serializer.dumps(info)  # bytes
        token = token.decode()

        # 发送邮件
        send_register_active_email.delay(email, username, token, user.id)
        # 4.返回响应数据
        return redirect(reverse('goods:index'))


class ActivateView(View):

    def get(self, request, token):
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            token_info = serializer.loads(token)
            user_id = token_info['confirm']
            user = User.objects.get(id=user_id)
            user.is_active = 1
            user.save()
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            # 捕获到异常说明过期，根据redis中的0号数据库存的token键取出对应的user_id
            user_id = StrictRedis(host='192.168.153.129', port=6379, db=0).get(token).decode()
            print(user_id)
            user = User.objects.get(id=user_id)
            serializer = Serializer(settings.SECRET_KEY, 3600)
            info = {"confirm": user_id}
            # 加密用户的身份信息，生成激活token
            token1 = serializer.dumps(info)  # bytes
            token1 = token1.decode()
            # 发送邮件
            send_register_active_email.delay(user.email, user.username, token1, user.id)
            return HttpResponse('<h2>激活链接已过期,新的激活链接已重新发送到你邮箱</h2>', content_type='text/html; charset=utf-8')


# /user/login
class LoginView(View):
    def get(self, request):
        '''显示登陆页面'''
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'user/login.html', {'username': username, 'checked': checked})

    def post(self, request):
        '''登陆校验'''
        # 接收数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        remember = request.POST.get('remember')

        # 校验数据
        if not all([username, password]):
            return render(request, 'user/login.html', {'errmsg': '数据不完整'})

        # 登陆校验
        user = authenticate(username=username, password=password)
        if user is not None and user.is_active:
            # 后台验证了用户名和密码存在,判断用户是否已激活
            login(request, user)
            next_url = request.GET.get('next', reverse('goods:index'))
            response = redirect(next_url)

            # 记住用户被勾选了
            if remember == 'on':
                # 记住用户名
                response.set_cookie('username', username, max_age=7 * 24 * 3600)
            else:
                response.delete_cookie('username')
            return response
        else:
            # 后台验证了用户名和密码不存在
            return render(request, 'user/login.html', {'errmsg': '用户名或密码错误,或者账号未激活'})


# /user/logout
class LogoutView(View):
    '''退出登录'''

    def get(self, request):
        logout(request)
        return redirect(reverse('goods:index'))


# /user
# @method_decorator(login_required, name='get')
# 使用类视图的扩展类Mixin来判断用户是否登录了
class UserInfoView(LoginRequireMixin, View):
    '''用户中心-信息页'''

    def get(self, request):
        # 如果当前用户尚未登录，则此属性将设置为实例AnonymousUser，返回空
        # 如果当前用户登录，则将为其实例User，返回user对象

        # 获取用户信息
        user = request.user
        address = Address.objects.get_default_address(user)

        # 获取用户最近浏览记录
        cn = get_redis_connection('default')
        history_key = 'history_%d' % user.id
        # 获取商品最近浏览记录的前5个id值
        goodsid_list = cn.lrange(history_key, 0, 4)
        # 按照商品的id号查询每个id对应的商品SKU详细信息
        goodshis_list = []
        for id in goodsid_list:
            goods = GoodsSKU.objects.get(id=id)
            goodshis_list.append(goods)
        # 配置上下文
        context = {'page': 'info', 'address': address, 'goodshis_list': goodshis_list}
        return render(request, 'user/user_center_info.html', context)


# /user/order
# 使用method_decorator类装饰器来判断用户是否登录了
@method_decorator(login_required, name='get')
class UserOrderView(View):
    '''用户中心-订单页'''

    def get(self, request):
        # 获取用户的全部订单
        return render(request, 'user/user_center_order.html', {'page': 'order'})


# /address
@method_decorator(login_required, name='get')
class AddressView(View):
    '''用户中心-地址页'''

    def get(self, request):
        # 获取用户的默认收货地址
        user = request.user
        address = Address.objects.get_default_address(user)
        return render(request, 'user/user_center_site.html', {'page': 'address', 'address': address})

    def post(self, request):
        # 接收前端发送过来的数据
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 判断数据的完整性
        if not all([receiver, addr, phone]):
            return render(request, 'user/user_center_site.html', {'errmsg': '数据不完整'})

        # 校验手机号
        if not re.match(r'^1[3|4|5|7|8]\d{9}$', phone):
            return render(request, 'user/user_center_site.html', {'errmsg': '手机号码格式有误'})

        # 获取当前登录对象
        user = request.user
        address = Address.objects.get_default_address(user)
        # 根据address的值设置is_defalut的值
        if address:
            is_default = False
        else:
            is_default = True

        # 添加地址信息
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)
        # 返回应答
        return redirect(reverse('user:address'))
