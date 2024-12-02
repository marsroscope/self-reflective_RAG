
## Quick Start
<font style="color:rgb(31, 35, 40);">1.首先需要以库形式安装我们的主系统，请执行：</font>

```plain
pip install git+https://github.com/yourusername/chatchat.git
```

2.执行初始化

```yaml
cd Medical_HAI
chatchat init
```

3.配置参数文件：

+ <font style="color:rgb(31, 35, 40);">配置模型（model_settings.yaml）   推荐使用glm4 plus apikey</font>

```yaml
api_key: YOUR_GLM4_plus_API_KEY
```

+ <font style="color:rgb(31, 35, 40);">配置基本参数（basic_settings.yaml）</font>

```yaml
# 知识库默认存储路径
KB_ROOT_PATH: {your_project_path}\data\knowledge_base

# 数据库默认存储路径。如果使用sqlite，可以直接修改DB_ROOT_PATH；如果使用其它数据库，请直接修改SQLALCHEMY_DATABASE_URI。
DB_ROOT_PATH: {your_project_path}\data\knowledge_base\info.db

# 知识库信息数据库连接URI
SQLALCHEMY_DATABASE_URI: sqlite:///{your_project_path}\data\knowledge_base\info.db

```

+ 配置你的bing_search_v7 api key<font style="color:rgb(31, 35, 40);">（basic_settings.yaml）</font>

需要注册一个bing官方的bing_search_v7服务。

```yaml
DEFAULT_BING_SEARCH_API_kEY:
```

5.启动项目

```yaml
chatchat start -a
```







