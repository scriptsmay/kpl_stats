// ============================================
// 无言粉丝应援站 · 主脚本
// ============================================

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
    { date: '2025-12-11', desc: '2025挑战者杯单败淘汰赛D6 · 马超 MVP' },
    { date: '2025-12-19', desc: '2025挑战者杯双败淘汰赛D1 · 关羽、马超、曹操 MVP' },
    { date: '2025-12-25', desc: '2025挑战者杯双败淘汰赛D4 · 夏洛特 MVP' },
    { date: '2026-01-15', desc: '2026KPL春季赛常规赛第一轮W1D2 · 狂铁 MVP' },
    { date: '2026-01-22', desc: '2026KPL春季赛常规赛第一轮W2D2 · 关羽 MVP' },
    { date: '2026-03-08', desc: '2026KPL春季赛常规赛第三轮W1D1 · 关羽 MVP' },
    { date: '2026-03-08', desc: '2026KPL春季赛常规赛第三轮W1D4 · 夏洛特 MVP' },
    { date: '2026-03-14', desc: '2026KPL春季赛常规赛第三轮W2D4 · 马超 MVP' },
    { date: '2026-03-18', desc: '2026KPL春季赛常规赛第三轮W3D1 · 关羽 MVP' },
    { date: '2026-03-21', desc: '2026KPL春季赛常规赛第三轮W3D4 · 吕布 MVP' },
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
    { date: '2025-12-09', desc: '以青训破军无言身份首次登上KPL赛场' },
    { date: '2025-12-29', desc: '以青训营状元身份加入KSG俱乐部，改名KSG无言' },
    { date: '2026-01-15', desc: '以KSG俱乐部首发对抗路登上KPL春季赛' },
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

  try {
    // TODO: 替换为真实API地址
    // const response = await fetch('https://data.kplwuyan.site/api/player/core-stats');
    // const data = await response.json();

    // 模拟数据 - 上线后替换为真实数据
    const data = { matches: 42, kills: 187, mvp: 12, winRate: 68.5 };

    container.innerHTML = `
            <div class="stat-card" data-aos="fade-up">
                <div class="stat-value">${data.matches}</div>
                <div class="stat-label">出场次数</div>
            </div>
            <div class="stat-card" data-aos="fade-up">
                <div class="stat-value">${data.kills}</div>
                <div class="stat-label">总击杀</div>
            </div>
            <div class="stat-card" data-aos="fade-up">
                <div class="stat-value">${data.mvp}</div>
                <div class="stat-label">MVP次数</div>
            </div>
            <div class="stat-card" data-aos="fade-up">
                <div class="stat-value">${data.winRate}%</div>
                <div class="stat-label">胜率</div>
            </div>
        `;
  } catch (error) {
    console.error('获取数据失败:', error);
    container.innerHTML = `
            <div class="stat-card">
                <div class="stat-value">--</div>
                <div class="stat-label">数据加载中</div>
            </div>
        `;
  }
}

// 获取博客最新文章（对接 Halo API）
async function fetchPosts() {
  const container = document.getElementById('blogGrid');
  if (!container) return;

  try {
    // TODO: 替换为真实API地址
    // const response = await fetch('https://blog.kplwuyan.site/api/content/posts?size=3');
    // const posts = await response.json();

    // 模拟数据 - 上线后替换为真实数据
    const posts = [
      {
        title: '无言专访：关于新赛季的目标与期待',
        excerpt: '在最近的采访中，无言分享了他对新赛季的看法...',
        date: '2026-03-20',
        cover: 'https://picsum.photos/400/200?random=1',
      },
      {
        title: '训练日记：团战意识提升之路',
        excerpt: '从个人技术到团队配合，无言的训练心得分享...',
        date: '2026-03-15',
        cover: 'https://picsum.photos/400/200?random=2',
      },
      {
        title: '品牌代言官宣',
        excerpt: '正式成为XX品牌代言人...',
        date: '2026-03-10',
        cover: 'https://picsum.photos/400/200?random=3',
      },
    ];

    container.innerHTML = posts
      .map(
        (p) => `
            <a href="https://blog.kplwuyan.site/post/${p.title.replace(/\s/g, '-')}" target="_blank" class="blog-card">
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
  } catch (error) {
    console.error('获取博客失败:', error);
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
  // 1天 = 24小时 * 60分钟 * 60秒 * 1000毫秒
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
