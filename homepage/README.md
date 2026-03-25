# Homepage 构建说明

## 目录结构

```
homepage/
├── package.json        # Node.js 依赖配置
├── build.js            # 构建脚本（自动生成配置 + 压缩）
├── dist/               # 构建输出目录（已加入 .gitignore）
├── config.js           # 自动生成的配置文件（不要手动修改，已加入 .gitignore）
├── config.production.json # 生产环境配置模板
├── config.example.js   # 配置示例文件
├── index.html          # 主页 HTML
└── assets/             # 静态资源
```

## 快速开始

### 安装依赖

```bash
cd homepage
npm install
```

### 开发

```bash
npm run dev
```

生成开发环境配置（不压缩）。

### 生产构建

```bash
npm run build
```

生成生产环境配置并压缩优化。

### 命令行直接构建

```bash
node build.js                    # 开发环境
node build.js production         # 生产环境
node build.js --env=production   # 生产环境（另一种写法）
```

## 构建功能

### 开发环境

- ✅ 生成 `config.js`（API 地址：`http://localhost:8001/api`）
- ✅ 复制所有文件到 `dist/` 目录
- ❌ 不压缩（便于调试）

### 生产环境

- ✅ 生成 `config.js`（API 地址：`https://data.kplwuyan.site/api`）
- ✅ 复制所有文件到 `dist/` 目录
- ✅ **压缩 HTML**（移除空白、注释，压缩内联 CSS/JS）
- ✅ 显示构建统计（文件数、总大小、压缩率）

## 输出示例

```
🔨 开始构建 (production 环境)...
📂 源目录：/path/to/homepage
📦 输出目录：/path/to/homepage/dist

📝 [1/4] 生成配置文件...
   ✅ config.js 已生成
   API_BASE_URL: https://data.kplwuyan.site/api

🗜️  [2/4] 压缩 HTML 文件...
   ✅ HTML 已压缩
   原始大小：13.29 KB
   压缩后：9.87 KB
   压缩率：25.7%

🧹 [3/4] 清理输出目录...
   ✅ 输出目录已准备就绪

📋 [4/4] 复制文件到输出目录...
   ✅ index.html
   ✅ config.js
   ✅ assets/
   ✅ favicon.svg

✅ 构建完成！

📊 构建统计:
   文件总数：15
   总大小：245.67 KB
```

## 自动化部署

执行 `./deploy.sh` 时会自动：
1. 运行 `npm install` 安装依赖
2. 运行 `npm run build` 构建生产版本
3. 将 `dist/` 目录上传到服务器

## 自定义配置

### 修改 API 地址

编辑 `config.production.json`：

```json
{
  "API_BASE_URL": "https://your-custom-domain.com/api"
}
```

### 修改压缩选项

编辑 `build.js` 中的 `minify` 配置：

```javascript
const minified = minify.sync(htmlContent, {
  collapseWhitespace: true,          // 移除空白
  removeComments: true,              // 移除注释
  removeRedundantAttributes: true,   // 移除冗余属性
  minifyCSS: true,                   // 压缩 CSS
  minifyJS: true,                    // 压缩 JS
  // ...
});
```

## 注意事项

- `config.js` 和 `dist/` 已加入 `.gitignore`，不会提交到 Git 仓库
- 生产环境务必使用 `npm run build:prod` 或 `node build.js production`
- 首次运行需要先执行 `npm install` 安装 `html-minifier-terser`
