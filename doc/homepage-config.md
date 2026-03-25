# Homepage 部署配置指南

## 环境配置

### 开发环境

1. 复制配置文件：
   ```bash
   cd homepage
   cp config.example.js config.js
   ```

2. 确认配置（默认就是本地开发）：
   ```javascript
   window.API_BASE_URL = 'http://localhost:8001';
   ```

3. 直接打开 `index.html` 或使用本地服务器：
   ```bash
   # 使用 Python 简单服务器
   python -m http.server 3000
   
   # 或使用 Node.js http-server
   npx http-server -p 3000
   ```

### 生产环境

1. 修改 `config.js`：
   ```javascript
   window.API_BASE_URL = 'https://data.kplwuyan.site/api';
   ```

2. 或者使用构建工具自动注入环境变量（可选）

## 配置文件说明

### `config.js`（需手动创建）

```javascript
// API 基础地址
window.API_BASE_URL = 'http://localhost:8001'; // 开发环境
// window.API_BASE_URL = 'https://data.kplwuyan.site/api'; // 生产环境
```

**注意**：`config.js` 文件已被添加到 `.gitignore`，不会被提交到 Git 仓库。

### `config.example.js`（模板文件）

配置文件的模板，包含所有可配置项的说明。

## 目录结构

```
homepage/
├── index.html           # 主页面（引入 config.js）
├── config.example.js    # 配置模板
├── config.js            # 实际配置（需手动创建，已加入 .gitignore）
├── assets/
│   ├── js/
│   │   └── index.js     # 主脚本（使用 window.API_BASE_URL）
│   ├── css/
│   │   └── style.css
│   └── lib/
└── favicon.svg
```

## 快速切换环境

### 方法 1：手动修改 config.js

```javascript
// 开发环境
window.API_BASE_URL = 'http://localhost:8001';

// 生产环境
window.API_BASE_URL = 'https://data.kplwuyan.site/api';
```

### 方法 2：使用多个配置文件（推荐）

创建不同环境的配置文件：

```bash
# 开发环境配置
cp config.example.js config.dev.js
# 修改 config.dev.js 中的 API_BASE_URL 为 http://localhost:8001

# 生产环境配置
cp config.example.js config.prod.js
# 修改 config.prod.js 中的 API_BASE_URL 为 https://data.kplwuyan.site/api
```

部署时根据环境选择对应的配置文件：

```bash
# 开发环境
cp config.dev.js config.js

# 生产环境
cp config.prod.js config.js
```

## 验证配置

打开浏览器控制台，输入：

```javascript
window.API_BASE_URL
```

应该显示当前配置的 API 地址。

---

**更新时间**：2026-03-25
