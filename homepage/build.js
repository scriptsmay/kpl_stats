#!/usr/bin/env node

/**
 * Homepage 构建脚本
 * 
 * 功能：
 * - 根据环境生成 config.js 文件
 * - 压缩 HTML 文件
 * - 复制静态资源到 dist 目录
 * 
 * 用法：
 *   node build.js                    # 默认开发环境
 *   node build.js production         # 生产环境
 *   node build.js --env=production   # 生产环境（另一种写法）
 */

const fs = require('fs');
const path = require('path');

// 解析命令行参数
const args = process.argv.slice(2);
let environment = 'development';

args.forEach(arg => {
  if (arg === 'production' || arg === '--env=production') {
    environment = 'production';
  } else if (arg === 'development' || arg === '--env=development') {
    environment = 'development';
  }
});

// 环境配置
const configs = {
  development: {
    API_BASE_URL: 'http://localhost:8001/api'
  },
  production: {
    API_BASE_URL: 'https://data.kplwuyan.site/api'
  }
};

const config = configs[environment];

if (!config) {
  console.error(`❌ 未知环境：${environment}`);
  console.error('支持的环境：development, production');
  process.exit(1);
}

// 目录配置
const ROOT_DIR = path.resolve(__dirname);
const SRC_DIR = ROOT_DIR;
const DIST_DIR = path.join(ROOT_DIR, 'dist');

console.log(`\n🔨 开始构建 (${environment} 环境)...`);
console.log(`📂 源目录：${SRC_DIR}`);
console.log(`📦 输出目录：${DIST_DIR}\n`);

// 主构建函数
async function build() {
  // 1. 生成 config.js
  console.log('📝 [1/4] 生成配置文件...');
  const configContent = `/**
 * Homepage 环境配置文件
 * 
 * 此文件由 build.js 自动生成，不要手动修改
 * 环境：${environment}
 * 生成时间：${new Date().toISOString()}
 */

// API 基础地址
window.API_BASE_URL = '${config.API_BASE_URL}';
`;

  const configPath = path.join(SRC_DIR, 'config.js');
  fs.writeFileSync(configPath, configContent, 'utf8');
  console.log(`   ✅ config.js 已生成`);
  console.log(`   API_BASE_URL: ${config.API_BASE_URL}\n`);

  // 2. 压缩 HTML
  console.log('🗜️  [2/4] 压缩 HTML 文件...');
  let htmlContent = fs.readFileSync(path.join(SRC_DIR, 'index.html'), 'utf8');
  let isCompressed = false;

  if (environment === 'production') {
    try {
      const htmlMinifierTerser = require('html-minifier-terser');
      const minify = htmlMinifierTerser.minify || htmlMinifierTerser.default.minify;
      
      const originalSize = fs.readFileSync(path.join(SRC_DIR, 'index.html'), 'utf8').length;
      htmlContent = await minify(htmlContent, {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        removeScriptTypeAttributes: true,
        removeStyleLinkTypeAttributes: true,
        minifyCSS: true,
        minifyJS: true
      });
      
      isCompressed = true;
      console.log(`   ✅ HTML 已压缩`);
      console.log(`   原始大小：${(originalSize / 1024).toFixed(2)} KB`);
      console.log(`   压缩后：${(htmlContent.length / 1024).toFixed(2)} KB`);
      console.log(`   压缩率：${((1 - htmlContent.length / originalSize) * 100).toFixed(1)}%\n`);
    } catch (error) {
      console.log(`   ⚠️  html-minifier-terser 未安装，跳过压缩`);
      console.log(`   运行 "npm install" 安装依赖以启用压缩功能\n`);
    }
  } else {
    console.log(`   ℹ️  开发环境，跳过压缩\n`);
  }

  // 3. 清理并创建 dist 目录
  console.log('🧹 [3/4] 清理输出目录...');
  if (fs.existsSync(DIST_DIR)) {
    fs.rmSync(DIST_DIR, { recursive: true, force: true });
  }
  fs.mkdirSync(DIST_DIR, { recursive: true });
  console.log(`   ✅ 输出目录已准备就绪\n`);

  // 4. 复制文件
  console.log('📋 [4/4] 复制文件到输出目录...');

  // 复制 HTML
  const htmlOutputPath = path.join(DIST_DIR, 'index.html');
  fs.writeFileSync(htmlOutputPath, htmlContent, 'utf8');
  console.log(`   ✅ index.html`);

  // 复制 config.js
  fs.copyFileSync(configPath, path.join(DIST_DIR, 'config.js'));
  console.log(`   ✅ config.js`);

  // 复制 assets 目录
  const assetsSrcDir = path.join(SRC_DIR, 'assets');
  const assetsDistDir = path.join(DIST_DIR, 'assets');
  if (fs.existsSync(assetsSrcDir)) {
    copyDirectory(assetsSrcDir, assetsDistDir);
    console.log(`   ✅ assets/`);
  }

  // 复制 favicon.svg
  const faviconSrc = path.join(SRC_DIR, 'favicon.svg');
  if (fs.existsSync(faviconSrc)) {
    fs.copyFileSync(faviconSrc, path.join(DIST_DIR, 'favicon.svg'));
    console.log(`   ✅ favicon.svg`);
  }

  console.log('');

  // 完成
  console.log('✅ 构建完成！\n');
  console.log('📊 构建统计:');
  const stats = getDirectoryStats(DIST_DIR);
  console.log(`   文件总数：${stats.fileCount}`);
  console.log(`   总大小：${(stats.totalSize / 1024).toFixed(2)} KB`);
  if (isCompressed) {
    console.log(`   ✨ 已启用生产优化\n`);
  }
}

/**
 * 递归复制目录
 */
function copyDirectory(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  const entries = fs.readdirSync(src, { withFileTypes: true });
  
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    
    if (entry.isDirectory()) {
      copyDirectory(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

/**
 * 获取目录统计信息
 */
function getDirectoryStats(dir) {
  let fileCount = 0;
  let totalSize = 0;
  
  function walk(currentDir) {
    const entries = fs.readdirSync(currentDir, { withFileTypes: true });
    for (const entry of entries) {
      const filePath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        walk(filePath);
      } else {
        fileCount++;
        totalSize += fs.statSync(filePath).size;
      }
    }
  }
  
  walk(dir);
  return { fileCount, totalSize };
}

// 执行构建
build().catch(err => {
  console.error('❌ 构建失败:', err);
  process.exit(1);
});
