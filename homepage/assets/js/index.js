AOS.init({ duration: 800, once: true, offset: 80 });

window.addEventListener('scroll', () => {
  const navbar = document.getElementById('navbar');
  if (window.scrollY > 50) navbar.classList.add('scrolled');
  else navbar.classList.remove('scrolled');
});

function toggleMobileMenu() {
  const navLinks = document.querySelector('.nav-links');
  if (navLinks.style.display === 'flex') {
    navLinks.style.display = '';
    navLinks.style.flexDirection = '';
    navLinks.style.position = '';
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

// 数据获取（模拟，上线后替换真实API）
async function fetchStats() {
  try {
    // 真实API: fetch('https://data.kplwuyan.site/api/player/core-stats')
    const data = { matches: 42, kills: 187, mvp: 8, winRate: 68.5 };
    document.getElementById('statsGrid').innerHTML = `
                <div class="stat-card" data-aos="fade-up"><div class="stat-value">${data.matches}</div><div class="stat-label">出场次数</div></div>
                <div class="stat-card" data-aos="fade-up"><div class="stat-value">${data.kills}</div><div class="stat-label">总击杀</div></div>
                <div class="stat-card" data-aos="fade-up"><div class="stat-value">${data.mvp}</div><div class="stat-label">MVP次数</div></div>
                <div class="stat-card" data-aos="fade-up"><div class="stat-value">${data.winRate}%</div><div class="stat-label">胜率</div></div>
            `;
  } catch (e) {
    console.error(e);
  }
}

async function fetchPosts() {
  try {
    // 真实API: fetch('https://blog.kplwuyan.site/api/content/posts?size=3')
    const posts = [
      {
        title: '无言专访：关于新赛季的目标',
        excerpt: '在最近的采访中，无言分享了...',
        date: '2026-03-20',
        cover: 'https://picsum.photos/400/200?random=1',
      },
      {
        title: '训练日记：团战意识提升之路',
        excerpt: '从个人技术到团队配合...',
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
    document.getElementById('blogGrid').innerHTML = posts
      .map(
        (p) => `
                <a href="https://blog.kplwuyan.site/post/${p.title.replace(/\s/g, '-')}" target="_blank" class="blog-card">
                    <img src="${p.cover}" class="blog-card-img">
                    <div class="blog-card-content">
                        <div class="blog-card-date">${p.date}</div>
                        <h3 class="blog-card-title">${p.title}</h3>
                        <p class="blog-card-excerpt">${p.excerpt}</p>
                    </div>
                </a>
            `,
      )
      .join('');
  } catch (e) {
    console.error(e);
  }
}

function loadFanworks() {
  const works = [
    { img: 'https://picsum.photos/400/300?random=20', author: '@小无言粉丝', type: '插画' },
    { img: 'https://picsum.photos/400/300?random=21', author: '@无言应援组', type: '应援手幅' },
    { img: 'https://picsum.photos/400/300?random=22', author: '@赛场记录君', type: '赛场摄影' },
  ];
  document.getElementById('fanworksGrid').innerHTML = works
    .map(
      (w) => `
            <div class="fanwork-card">
                <img src="${w.img}" class="fanwork-img">
                <div class="fanwork-content">
                    <div>${w.type}</div>
                    <div class="fanwork-author">by ${w.author}</div>
                </div>
            </div>
        `,
    )
    .join('');
}

document.addEventListener('DOMContentLoaded', () => {
  fetchStats();
  fetchPosts();
  loadFanworks();
});
