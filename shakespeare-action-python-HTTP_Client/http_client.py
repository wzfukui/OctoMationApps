# -*- coding: utf-8 -*-
import requests
import time
import os
import json
import uuid
from urllib.parse import urlparse
from http.cookiejar import Cookie, CookieJar, MozillaCookieJar

SUPPORTED_METHODS = {"GET", "HEAD", "DELETE", "OPTIONS", "POST", "PUT", "PATCH"}


def parse_bool(value, default):
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        value = value.strip().lower()
        if value in ("true", "1", "yes", "y", "on", "是"):
            return True
        if value in ("false", "0", "no", "n", "off", "否"):
            return False
    raise ValueError(f"Invalid boolean value: {value}")


def parse_timeout(value, default):
    if value is None or value == "":
        return default
    timeout = int(value)
    if timeout <= 0:
        raise ValueError("TIMEOUT must be greater than 0")
    return timeout


def get_param(params, key, default=""):
    value = params.get(key, default)
    if value is None:
        return default
    return value


def parse_headers(header_text):
    headers = {}
    for headline in str(header_text).splitlines():
        headline = headline.strip()
        if not headline:
            continue
        if ':' not in headline:
            raise ValueError(f"Invalid HEADER line, expected KEY:VALUE: {headline}")
        key, value = headline.split(':', 1)
        key = key.strip()
        value = value.strip()
        if key and value:
            headers[key] = value
    return headers


def save_cookie_to_file(obj_cookie_jar, cookie_file):
    """
    将CookieJar对象转换为MozillaCookieJar，并存储到文件
    """
    cookie_dir = os.path.dirname(cookie_file)
    if cookie_dir:
        os.makedirs(cookie_dir, exist_ok=True)
    mozilla_cookiejar = MozillaCookieJar()
    for cookie in obj_cookie_jar:
        mozilla_cookiejar.set_cookie(cookie)
    mozilla_cookiejar.save(cookie_file, ignore_discard=True, ignore_expires=True)

def load_cookie_from_file(cookie_file):
    """
    从文件加载MozillaCookieJar对象，并转换成CookieJar对象
    """
    cookiejar = CookieJar()
    if os.path.exists(cookie_file):
        mozilla_cookiejar = MozillaCookieJar()
        try:
            mozilla_cookiejar.load(cookie_file, ignore_discard=True, ignore_expires=True)
            for cookie in mozilla_cookiejar:
                cookiejar.set_cookie(cookie)
        except Exception as e:
            print(e)
    return cookiejar

def from_string_to_cookiejar(cookie_string, domain):
    """
    将Cookie字符串转换为CookieJar对象，如："vk=70acfa88; cbc-sid=20493701 "
    """
    cookie_jar = CookieJar()
    for item in cookie_string.split(';'):
        item = item.strip()
        if not item:
            continue
        if '=' not in item:
            raise ValueError(f"Invalid COOKIES item, expected name=value: {item}")
        name, value = item.split('=', 1)
        name = name.strip()
        value = value.strip()
        if not name:
            raise ValueError("Invalid COOKIES item, empty cookie name")
        cookie = Cookie(
            version=0,
            name=name,
            value=value,
            port=None,
            port_specified=False,
            domain=domain,
            domain_specified=False,
            domain_initial_dot=False,
            path='/',
            path_specified=True,
            secure=False,
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={'HttpOnly': None},
            rfc2109=False,
        )
        cookie_jar.set_cookie(cookie)
    return cookie_jar

def from_cookiejar_to_string(cookiejar):
    """
    将CookieJar对象转换成Cookie字符串，用于HTTP请求中的HEAD
    """
    cookie_string = ''
    if isinstance(cookiejar, CookieJar):
        for cookie in cookiejar:
            cookie_string += f'{cookie.name}={cookie.value}; '
        # Remove the trailing semicolon and space
        cookie_string = cookie_string[:-2]
    return cookie_string

def http_request(params, assets, context_info):
    """通用HTTP请求"""

    # 返回值
    json_ret = {
        "code": 200, 
        "msg": "",
        "data": {
            "http_response_code": 0, 
            "http_response_text": "", 
            "http_response_headers": {}, 
            "cookies": "",
            "cookie_file": ""
        }
    }

    try:
        if params is None:
            params = {}

        # URL服务器，如：https://user:pass@example.com:8080
        SERVER = str(get_param(params, "SERVER")).strip()
        if not SERVER:
            raise ValueError("SERVER is required")
        if SERVER.endswith('/'):
            SERVER = SERVER[:-1]
        parsed_server = urlparse(SERVER)
        if parsed_server.scheme not in ("http", "https") or not parsed_server.netloc:
            raise ValueError("SERVER must include http:// or https:// and a host")

        # URL路径，如：/user/info，默认为：/
        PATH = str(get_param(params, "PATH", "/")).strip()
        if PATH == "":
            PATH = "/"
        if PATH != "/" and not PATH.startswith('/'):
            PATH = f"/{PATH}"

        # URL请求参数(不带?，需自行做好URL Encode，如：user=Chris&comment=I%20love%20OctoMation）
        QUERY = str(get_param(params, "QUERY")).strip()
        if QUERY.startswith('?'):
            QUERY = QUERY[1:]

        # HTTP请求头中的User Agent，默认为：OctoMation-HTTP-Client v1.0.0
        USER_AGENT = str(get_param(params, "USER_AGENT", "OctoMation-HTTP-Client v1.0.0")).strip()
        if USER_AGENT == "":
            USER_AGENT = "OctoMation-HTTP-Client v1.0.0"

        # HTTP请求头中的Content-Type，默认：空
        CONTENT_TYPE = str(get_param(params, "CONTENT_TYPE")).strip()
        # 自定义HTTP头，KEY:VALUE，按行填写。
        HEADER = get_param(params, "HEADER")
        # HTTP请求体（Form模式需要自行URL Encode）
        BODY = str(get_param(params, "BODY"))
        # HTTP请求方法，默认：GET
        METHOD = str(get_param(params, "METHOD", "GET")).strip().upper()
        if METHOD == "":
            METHOD = "GET"
        if METHOD not in SUPPORTED_METHODS:
            raise ValueError(f"Unsupported HTTP method: {METHOD}")

        COOKIES = str(get_param(params, "COOKIES")).strip()
        json_ret['data']['cookies'] = COOKIES

        COOKIE_FILE = ""
        cookie_file_param = get_param(params, "COOKIE_FILE")
        if cookie_file_param != "":
            if '__RANDOM__COOKIE__FILE__' == cookie_file_param:
                COOKIE_FILE = f'/tmp/cookie.{int(time.time()*1000)}.{uuid.uuid4().hex}.pkl'
            else:
                COOKIE_FILE = str(cookie_file_param).strip()
            if COOKIE_FILE and not os.path.exists(COOKIE_FILE):
                save_cookie_to_file(CookieJar(), COOKIE_FILE)
        json_ret['data']['cookie_file'] = COOKIE_FILE

        # 代理服务器
        PROXY = None
        proxy_param = get_param(params, "PROXY")
        if proxy_param != "":
            proxy_value = str(proxy_param).strip()
            PROXY = {
                "http": proxy_value,
                "https": proxy_value
            }

        VERIFY_SSL = parse_bool(get_param(params, "VERIFY_SSL", True), True)
        ALLOW_REDIRECTS = parse_bool(get_param(params, "ALLOW_REDIRECTS", True), True)
        TIMEOUT = parse_timeout(get_param(params, "TIMEOUT", 60), 60)

        # 拼接完整URL
        url = f"{SERVER}{PATH}"
        if QUERY != "":
            url = f"{SERVER}{PATH}?{QUERY}"

        # 准备HTTP HEAD字典
        headers = parse_headers(HEADER)
        if CONTENT_TYPE != "":
            headers['content-type'] = CONTENT_TYPE
        if USER_AGENT != "":
            headers['user-agent'] = USER_AGENT

        # COOKIES字符串存在的情况下，优先使用COOKIES
        if COOKIES != "":
            domain = urlparse(url).hostname
            cookies_for_request = from_string_to_cookiejar(COOKIES, domain)
        elif COOKIE_FILE != "":
            cookies_for_request = load_cookie_from_file(COOKIE_FILE)
        else:
            cookies_for_request = CookieJar()

        s = requests.session()
        if cookies_for_request:
            s.cookies = cookies_for_request

        request_kwargs = {
            "url": url,
            "headers": headers,
            "allow_redirects": ALLOW_REDIRECTS,
            "proxies": PROXY,
            "verify": VERIFY_SSL,
            "timeout": TIMEOUT
        }
        if METHOD in ("POST", "PUT", "PATCH"):
            request_kwargs["data"] = BODY.encode("utf-8")
        res = s.request(METHOD, **request_kwargs)
        
        if res is not None:
            for cookie in s.cookies:
                cookies_for_request.set_cookie(cookie)
            if COOKIE_FILE != "":
                save_cookie_to_file(cookies_for_request, COOKIE_FILE)
            json_ret['data']['http_response_code'] = res.status_code
            json_ret['data']['http_response_text'] = res.text
            json_ret['data']['http_response_headers'] =json.loads(json.dumps(dict(res.headers)))
            json_ret['data']['cookies'] = from_cookiejar_to_string(cookies_for_request)

        if 200 <= json_ret['data']['http_response_code'] < 300:
            json_ret['msg'] = "请求发送成功，请确认返回结果:)"
        else:
            json_ret['msg'] = "可能请求失败，请检查错误信息:("
    except Exception as e:
        json_ret['code']= 500
        json_ret["msg"] = str(e)

    return json_ret
