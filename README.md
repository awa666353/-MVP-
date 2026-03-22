# 全国医院公开信息采集系统（MVP）

## 环境

- Python 3.10+

## 安装

```bash
pip install -r requirements.txt
```

可选（JS 渲染页面兜底）：

```bash
pip install -r requirements-playwright.txt
playwright install chromium
```

## 运行

```bash
python main.py --input data/seeds.csv --limit 10
```

常用参数：

- `--db`：SQLite 路径（默认 `data/hospitals.sqlite`）
- `--no-robots`：忽略 robots.txt（仅调试用）
- `--no-export`：不导出 CSV/JSON
- `--log-level DEBUG`

导出文件默认在 `data/exports/`。

## 模块说明

见下文「项目目录结构」或仓库内各包 `__init__.py` 与中文注释。
