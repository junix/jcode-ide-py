
set shell := ["bash", "-euo", "pipefail", "-c"]

# 解释型脚本安装目录（与架构无关，ADR-749）
install_bin := home_directory() / "sync" / "bin"
# 构建（Release 模式）
build:
    uv build

# 运行测试
test:
    uv run -m pytest src/jcode_ide/tests/ -v

# 安装到 ~/sync/bin/
install: build
    @echo "Library package — no binary to install"
