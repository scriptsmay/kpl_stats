# 通过这个接口可以查询KSG队伍的信息，其中就包括无言的 部分 个人数据
curl 'https://kplshop-op.timi-esports.qq.com/kplow/getTeamsIntro' \
  -H 'accept: application/json, text/plain, */*' \
  -H 'accept-language: zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7' \
  -H 'content-type: application/json' \
  -H 'dnt: 1' \
  -H 'origin: https://kpl.qq.com' \
  -H 'priority: u=1, i' \
  -H 'referer: https://kpl.qq.com/' \
  -H 'sec-ch-ua: "Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-site' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36' \
  --data-raw '{"teamid":"KPL2026S1_ytg"}'


获取赛季日期: http://47.102.210.150:5006/season/KPL2026S1
可得出 赛季日期范围: 2026-01-13 ~ 2026-04-12
获取赛事回顾数据: http://47.102.210.150:5022/api/records?season=KPL2026S1
获取新的选手数据: http://47.102.210.150:5035/api/all-player-stats?season=KPL2026S1
获取战队赛季数据: http://47.102.210.150:5012/api/team-season-summary/KPL2026S1
获取选手能力数据: http://47.102.210.150:5035/api/player-abilities/KPL2026S1
KSG成员数据：http://47.102.210.150:5006/KPL2026S1/KSG

---

战力系统官方页面：http://www.jungushiyan.cn/gaojie/jiaoshou/jiaoshou.html

我有一个数据接口，获取KPL无言选手职业生涯数据： 
http://47.102.210.150:5049/api/player-career?player_name=KSG.%E6%97%A0%E8%A8%80&season_type=all
返回数据格式如 career.json 附件所示，而附件 result.html 是数据最终呈现的结构。
我需要你实现一个完整的 data.html 的代码，将 接口中的数据按照 result.html 中的结构进行展示。
将代码提供给我。