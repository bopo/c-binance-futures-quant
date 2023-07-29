from dynaconf import Dynaconf

MYSQL_CONFIG = {
    'host': '',
    'port': 3306,
    'user': '',
    'password': '',
    'database': '',
    'charset': 'utf8mb4'
}

FEISHU_APP_ID = ""

FEISHU_APP_SECRET = ""

WS_ADDRESS_A = ""  # ws://172.0.0.0:3698

WS_ADDRESS_B = ""

ALIYUN_API_KEY = ""

ALIYUN_API_SECRET = ""

ALIYUN_POINT = "ap-northeast-1"

WEB_ADDRESS = ""  # 172.0.0.0

CANCEL_WEB_ADDRESS = ""  # 172.0.0.0

settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.yaml', '.secrets.yaml'],

    MYSQL_CONFIG=MYSQL_CONFIG,

    FEISHU_APP_ID=FEISHU_APP_ID,
    FEISHU_APP_SECRET=FEISHU_APP_SECRET,

    WS_ADDRESS_A=WS_ADDRESS_A,  # ws://172.0.0.0:3698
    WS_ADDRESS_B=WS_ADDRESS_B,

    ALIYUN_API_KEY=ALIYUN_API_KEY,
    ALIYUN_API_SECRET=ALIYUN_API_SECRET,
    ALIYUN_POINT=ALIYUN_POINT,

    WEB_ADDRESS=WEB_ADDRESS,  # 172.0.0.0
    CANCEL_WEB_ADDRESS=CANCEL_WEB_ADDRESS,  # 172.0.0.0
)
