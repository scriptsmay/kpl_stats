// ============================================
// 无言粉丝应援站 · 主脚本
// ============================================

// API 配置（支持环境变量覆盖）
// 开发环境：http://localhost:8001
// 生产环境：https://data.kplwuyan.site/api
const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8001';

// 初始化 AOS 动画
AOS.init({
  duration: 800,
  once: true,
  offset: 80,
});

// 导航栏滚动效果
window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (window.scrollY > 50) {
    navbar.classList.add('scrolled');
  } else {
    navbar.classList.remove('scrolled');
  }
});

// 移动端菜单切换
function toggleMobileMenu() {
  const navLinks = document.querySelector('.nav-links');
  if (navLinks.style.display === 'flex') {
    navLinks.style.display = '';
    navLinks.style.flexDirection = '';
    navLinks.style.position = '';
    navLinks.style.top = '';
    navLinks.style.left = '';
    navLinks.style.right = '';
    navLinks.style.background = '';
    navLinks.style.padding = '';
    navLinks.style.gap = '';
    navLinks.style.borderBottom = '';
  } else {
    navLinks.style.display = 'flex';
    navLinks.style.flexDirection = 'column';
    navLinks.style.position = 'absolute';
    navLinks.style.top = '70px';
    navLinks.style.left = '0';
    navLinks.style.right = '0';
    navLinks.style.background = 'var(--bg-dark)';
    navLinks.style.padding = '1.5rem';
    navLinks.style.gap = '1rem';
    navLinks.style.borderBottom = '1px solid var(--border)';
  }
}

// ========== 数据加载函数 ==========

// 加载国服英雄列表
function loadHeroes() {
  const heroes = [
    '司空震',
    '杨戬',
    '狂铁',
    '马超',
    '曹操',
    '姬小满',
    '关羽',
    '夏洛特',
    '花木兰',
    '孙策',
    '李信',
    '影',
    '吕布',
    '蚩奼',
  ];
  const container = document.getElementById('heroesGrid');
  if (container) {
    container.innerHTML = heroes.map((hero) => `<span class="hero-tag">🏅 ${hero}</span>`).join('');
  }
}

// 加载生涯高光时刻
function loadHighlights() {
  const highlights = [
    { date: '2025-12-11', desc: '2025 挑战者杯单败淘汰赛 D6 · 马超 MVP' },
    { date: '2025-12-19', desc: '2025 挑战者杯双败淘汰赛 D1 · 关羽、马超、曹操 MVP' },
    { date: '2025-12-25', desc: '2025 挑战者杯双败淘汰赛 D4 · 夏洛特 MVP' },
    { date: '2026-01-15', desc: '2026KPL 春季赛常规赛第一轮 W1D2 · 狂铁 MVP' },
    { date: '2026-01-22', desc: '2026KPL 春季赛常规赛第一轮 W2D2 · 关羽 MVP' },
    { date: '2026-03-08', desc: '2026KPL 春季赛常规赛第三轮 W1D1 · 关羽 MVP' },
    { date: '2026-03-08', desc: '2026KPL 春季赛常规赛第三轮 W1D4 · 夏洛特 MVP' },
    { date: '2026-03-14', desc: '2026KPL 春季赛常规赛第三轮 W2D4 · 马超 MVP' },
    { date: '2026-03-18', desc: '2026KPL 春季赛常规赛第三轮 W3D1 · 关羽 MVP' },
    { date: '2026-03-21', desc: '2026KPL 春季赛常规赛第三轮 W3D4 · 吕布 MVP' },
  ];
  const container = document.getElementById('highlightsList');
  if (container) {
    container.innerHTML = highlights
      .map(
        (h) => `
            <div class="highlight-item">
                <div class="highlight-date">🏆 ${h.date}</div>
                <div class="highlight-desc">${h.desc}</div>
            </div>
        `,
      )
      .join('');
  }
}

// 加载职业生涯时间线
function loadCareer() {
  const career = [
    { date: '2025-12-09', desc: '以青训破军无言身份首次登上 KPL 赛场' },
    { date: '2025-12-29', desc: '以青训营状元身份加入 KSG 俱乐部，改名 KSG 无言' },
    { date: '2026-01-15', desc: '以 KSG 俱乐部首发对抗路登上 KPL 春季赛' },
  ];
  const container = document.getElementById('careerList');
  if (container) {
    container.innerHTML = career
      .map(
        (c) => `
            <div class="highlight-item" style="border-left-color: var(--secondary);">
                <div class="highlight-date">📅 ${c.date}</div>
                <div class="highlight-desc">${c.desc}</div>
            </div>
        `,
      )
      .join('');
  }
}

// 获取生涯数据（对接 FastAPI）
async function fetchStats() {
  const container = document.getElementById('statsGrid');
  if (!container) return;

  // 显示加载状态
  container.innerHTML = `
    <div class="stat-card loading">
      <div class="skeleton" style="width: 60px; height: 40px; margin: 0 auto"></div>
    </div>
    <div class="stat-card loading">
      <div class="skeleton" style="width: 60px; height: 40px; margin: 0 auto"></div>
    </div>
    <div class="stat-card loading">
      <div class="skeleton" style="width: 60px; height: 40px; margin: 0 auto"></div>
    </div>
    <div class="stat-card loading">
      <div class="skeleton" style="width: 60px; height: 40px; margin: 0 auto"></div>
    </div>
  `;

  try {
    const response = await fetch(`${API_BASE_URL}/player/career?season_type=all`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '数据加载失败');
    }

    const data = result.data.career_summary;

    // 根据实际返回的数据结构调整字段映射
    container.innerHTML = `
      <div class="stat-card" data-aos="fade-up">
        <div class="stat-value">${data.matches ?? data.total_matches ?? '--'}</div>
        <div class="stat-label">出场次数</div>
      </div>
      <div class="stat-card" data-aos="fade-up">
        <div class="stat-value">${data.kills ?? data.total_kills ?? '--'}</div>
        <div class="stat-label">总击杀</div>
      </div>
      <div class="stat-card" data-aos="fade-up">
        <div class="stat-value">${data.mvp ?? data.mvp_count ?? '--'}</div>
        <div class="stat-label">MVP 次数</div>
      </div>
      <div class="stat-card" data-aos="fade-up">
        <div class="stat-value">${data.total_assists ?? data.total_assists ?? '--'}</div>
        <div class="stat-label">总助攻</div>
      </div>
    `;

    console.log('[Stats] 数据加载成功:', result.message);
  } catch (error) {
    console.error('[Stats] 获取数据失败:', error);
    container.innerHTML = `
      <div class="stat-card">
        <div class="stat-value">--</div>
        <div class="stat-label">数据加载失败</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">--</div>
        <div class="stat-label">请稍后重试</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">--</div>
        <div class="stat-label">数据加载失败</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">--</div>
        <div class="stat-label">请稍后重试</div>
      </div>
    `;
  }
}

// 获取博客最新文章（对接后端 Halo API 代理）
async function fetchPosts() {
  const container = document.getElementById('blogGrid');
  if (!container) return;

  // 显示加载状态
  container.innerHTML = `
    <div class="blog-card loading"><div class="skeleton" style="height: 180px"></div></div>
    <div class="blog-card loading"><div class="skeleton" style="height: 180px"></div></div>
    <div class="blog-card loading"><div class="skeleton" style="height: 180px"></div></div>
  `;

  try {
    const response = await fetch(`${API_BASE_URL}/blog/posts?size=3`);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();

    if (result.code !== 200) {
      throw new Error(result.message || '博客加载失败');
    }

    // 后端已精简数据：{ items: [{ title, cover, excerpt, publishTime, permalink }] }
    const haloData = result.data;
    const items = haloData.items || [];

    if (items.length === 0) {
      container.innerHTML = `
        <div class="blog-card">
          <div class="blog-card-content">
            <p class="blog-card-excerpt">暂无文章</p>
          </div>
        </div>
      `;
      return;
    }

    const posts = items.map((item) => {
      // 处理封面图
      let cover = item.cover || 'https://picsum.photos/400/200?random=1';

      // 处理发布日期
      const publishTime = item.publishTime;
      const date = publishTime ? new Date(publishTime).toISOString().split('T')[0] : '未知日期';

      // 处理摘要：截断过长文本（最多 120 个字符）
      let excerpt = item.excerpt || '暂无摘要';
      if (excerpt.length > 120) {
        excerpt = excerpt.substring(0, 120) + '...';
      }

      return {
        title: item.title || '无标题',
        excerpt: excerpt,
        date: date,
        cover: cover,
        permalink: item.permalink || '#',
      };
    });

    container.innerHTML = posts
      .map(
        (p) => `
            <a href="https://blog.kplwuyan.site${p.permalink}" target="_blank" class="blog-card">
                <img src="${p.cover}" class="blog-card-img" alt="${p.title}" onerror="this.src='https://picsum.photos/400/200?random=1'">
                <div class="blog-card-content">
                    <div class="blog-card-date">${p.date}</div>
                    <h3 class="blog-card-title">${p.title}</h3>
                    <p class="blog-card-excerpt">${p.excerpt}</p>
                </div>
            </a>
        `,
      )
      .join('');

    console.log('[Posts] 博客加载成功:', result.message);
  } catch (error) {
    console.error('[Posts] 获取博客失败:', error);
    // 错误时显示默认文章（降级处理）
    const fallbackPosts = [
      {
        title: '博客加载中',
        excerpt: '正在连接博客数据，请稍后刷新页面重试',
        date: new Date().toISOString().split('T')[0],
        cover: 'https://picsum.photos/400/200?random=1',
      },
    ];

    container.innerHTML = fallbackPosts
      .map(
        (p) => `
            <a href="https://blog.kplwuyan.site" target="_blank" class="blog-card">
                <img src="${p.cover}" class="blog-card-img" alt="${p.title}">
                <div class="blog-card-content">
                    <div class="blog-card-date">${p.date}</div>
                    <h3 class="blog-card-title">${p.title}</h3>
                    <p class="blog-card-excerpt">${p.excerpt}</p>
                </div>
            </a>
        `,
      )
      .join('');
  }
}

// 计算年龄
function getAge() {
  const birthText = '2007-02-05';
  const birthDate = new Date(birthText);
  const today = new Date();

  // 1. 计算年龄
  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();
  const dayDiff = today.getDate() - birthDate.getDate();

  // 如果当前月份小于出生月份，或者月份相等但日期还没到，年龄减一
  if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
    age--;
  }

  // 2. 计算距离下一个生日还有几天
  // 先设定今年的生日
  let nextBirthday = new Date(today.getFullYear(), birthDate.getMonth(), birthDate.getDate());

  // 如果今年的生日已经过了，就计算明年的生日
  if (today > nextBirthday) {
    nextBirthday.setFullYear(today.getFullYear() + 1);
  }

  // 计算时间差（毫秒），然后转为天数
  // 1 天 = 24 小时 * 60 分钟 * 60 秒 * 1000 毫秒
  const diffTime = nextBirthday - today;
  const daysUntilBirthday = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return {
    age: age,
    daysUntilBirthday: daysUntilBirthday,
  };
}

// 页面加载时执行
document.addEventListener('DOMContentLoaded', () => {
  loadHeroes();
  loadHighlights();
  loadCareer();
  fetchStats();
  fetchPosts();

  const result = getAge();
  // console.log(`当前：${result.age}岁`);
  console.log(`距离下次生日还有：${result.daysUntilBirthday}天`);

  document.getElementById('age').textContent = result.age;
});
