
# 广州南方学院PC志愿者服务队订单申报系统 - 后端服务

[![Django Version](https://img.shields.io/badge/Django-5.1-green)](https://www.djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/)

这是与前端项目 [pc-declaration-system](https://github.com/shikaiwe/pc-declaration-system) 配套的后端服务，为广州南方学院PC志愿者服务队提供完整的工单申报和管理解决方案。

## 目录
- [系统架构](#系统架构)
- [功能模块](#功能模块)
- [API设计](#api设计)
- [开发指南](#开发指南)
- [部署指南](#部署指南)
- [测试方案](#测试方案)
- [协作信息](#协作信息)
- [许可证](#许可证)

## 系统架构

### 技术栈
| 组件 | 技术选择 |
|------|----------|
| 后端框架 | Django 5.1 |
| 数据库 | SQLite (开发) |
| 日志系统 | Loguru |
| API文档 | 模块内嵌Markdown文档 |
| 认证方式 | JWT + Session混合认证 |

### 项目结构
```
NanFangCollegePC/
├── common/          # 公共模型和工具
├── dashboard/       # 工单管理核心逻辑
├── login/           # 用户认证系统
├── register/        # 用户注册流程
├── SMS/             # 电子邮箱验证服务
├── unit/            # 实用工具(天气/IP等)
└── NanFangCollegePC/ # 项目配置
```

## 功能模块

### 核心功能
1. **用户认证系统**
   - 账号密码登录
   - 邮箱验证码注册账号
   - 密码找回功能
   - 自动登录机制

2. **工单管理系统**
   - 工单创建与提交
   - 工单分配与转派
   - 处理进度跟踪
   - 历史记录查询

3. **实时聊天室**
   - 像微信QQ一样聊天
   - 根据订单划分不同的聊天室
   - 现已支持发送图片

4. **辅助服务**
   - 电子邮箱验证码服务
   - 天气信息查询
   - 用户IP记录

## API设计

### 响应格式
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {
        // 业务数据
    }
}
```

### 状态码规范
| 状态码 | 含义 |
|--------|------|
| 200 | 请求成功 |
| 400 | 参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 500 | 服务器错误 |

## 开发指南

### 环境配置
1. 克隆仓库
```bash
git clone https://github.com/your-repo/NanFangCollegePC.git
cd NanFangCollegePC
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate    # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 数据库迁移
```bash
python manage.py migrate
```

5. 启动开发服务器
```bash
python manage.py runserver 0.0.0.0:8000
```

## 部署指南

### 生产环境要求
- Linux服务器
- Python 3.10+
- SQLite
- Nginx

### 部署步骤
1. 配置Nginx
```nginx
server {
        server_name localhost;
        listen 443 ssl;
        ssl_certificate /etc/nginx/sslkey/ssl.crt;
        ssl_certificate_key /etc/nginx/sslkey/ssl.key;
        ssl_session_timeout 5m;
        ssl_protocols TLSv1.2;
        ssl_ciphers EECDH+AESGCM:EDH+AESGCM:AES256+EECDH:AES256+EDH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK:!KRB5:!aECDH:!EDH+3DES;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
        location /api/{
                proxy_pass http://localhost:8000/api/;
        }
        location ~*\.html$ {
                root /root/WebFont/pc-declaration-system;
        }
        location ~*\.js$ {
                root /root/WebFont/pc-declaration-system/js;
        }
}
}

```

2. 启动服务
```bash
python manage.py runserver 0.0.0.0:8000
```

## 测试方案

### 测试类型
1. 单元测试
```bash
python manage.py test
```

2. API测试
- 使用Postman测试集合
- 自动化测试脚本

3. 压力测试
- Locust性能测试

## 协作信息

### 开发团队
| 角色 | 开发者 | 仓库 |
|------|--------|------|
| 前端 | shikaiwe | [pc-declaration-system](https://github.com/shikaiwe/pc-declaration-system) |
| 后端 | luogangsama | 当前仓库 |

### 协作流程
1. 使用Git Flow工作流
2. 提交Pull Request前运行测试
3. 重大变更需更新API文档

## 许可证
MIT License
