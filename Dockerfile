# ---- 阶段 1: 构建器 (Builder) ----
FROM python:3.12-bullseye as builder

# 安装编译 uvloop/httptools 等所需的系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 仅复制依赖文件以提升缓存命中率
COPY requirements.txt .

# 在构建器阶段安装所有依赖到 /install
# 在构建器阶段安装所有依赖到 /install
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# ---- 阶段 2: 最终镜像 (Final Image) ----
FROM python:3.12-slim

WORKDIR /app

LABEL name="DouK-Downloader" authors="JoeanAmier" repository="https://github.com/fetsfan/TikTokDownloader"

# 复制依赖到最终镜像
COPY --from=builder /install /usr/local

# 复制应用文件
COPY src /app/src
COPY locale /app/locale
COPY static /app/static
COPY license /app/license
COPY main.py /app/main.py
COPY api_main.py /app/api_main.py
COPY healthcheck.py /app/healthcheck.py

# 预置 settings.json -> Web API 模式（写入到 /app/Volume）
RUN python - <<'PY'
import json, os
os.makedirs('/app/Volume', exist_ok=True)
p = '/app/Volume/settings.json'
d = {'run_command': '7'}
with open(p, 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=4)
PY

# 预置数据库：跳过免责声明与语言选择
RUN python - <<'PY'
import sqlite3, os
os.makedirs('/app/Volume', exist_ok=True)
db = '/app/Volume/DouK-Downloader.db'
conn = sqlite3.connect(db)
cur = conn.cursor()
cur.executescript('''
CREATE TABLE IF NOT EXISTS config_data (
  NAME TEXT PRIMARY KEY,
  VALUE INTEGER NOT NULL CHECK(VALUE IN (0, 1))
);
CREATE TABLE IF NOT EXISTS option_data (
  NAME TEXT PRIMARY KEY,
  VALUE TEXT NOT NULL
);
''')
cur.execute('INSERT OR REPLACE INTO config_data (NAME, VALUE) VALUES (?, ?)', ('Disclaimer', 1))
cur.execute('INSERT OR REPLACE INTO option_data (NAME, VALUE) VALUES (?, ?)', ('Language', 'zh_CN'))
conn.commit()
conn.close()
PY

# 可选：API 令牌（公开部署务必设置强随机值）
ENV DOUK_TOKEN=fantes

EXPOSE 5555
VOLUME /app/Volume

# 拷贝并使用入口脚本，保证挂载卷内完成初始化再启动主程序
COPY docker_entry.py /app/docker_entry.py
HEALTHCHECK --interval=10s --timeout=3s --start-period=40s --retries=3 \
  CMD python /app/healthcheck.py || exit 1
CMD ["python", "docker_entry.py"]