/**
 * 丫丫计时器 — Cloudflare Worker 通知代理
 *
 * 部署方式：
 *   1. 打开 https://dash.cloudflare.com → Workers & Pages → 创建 Worker
 *   2. 把这个文件内容粘贴进去 → 部署
 *   3. 获得 URL 如 https://yaya-timer.你的用户名.workers.dev
 *   4. 在计时器页面「📝 更多」→ Worker URL 栏填入这个地址 → 保存
 *
 * 免费额度：10 万次/天，无需信用卡，全球 CDN 国内可用
 */

export default {
  async fetch(request, env, ctx) {
    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      });
    }

    if (request.method !== 'POST') {
      return json({ success: false, reason: '仅支持 POST' }, 405);
    }

    try {
      const params = await request.json();
      const channel = params.channel || 'qmsg';

      if (channel === 'serverchan') {
        return await handleServerChan(params);
      } else {
        return await handleQmsg(params);
      }
    } catch (e) {
      return json({ success: false, reason: 'JSON 解析失败: ' + e.message }, 400);
    }
  },
};

/** Server酱 微信推送 */
async function handleServerChan(params) {
  const key = params.key || '';
  if (!key) {
    return json({ success: false, reason: 'SendKey 不能为空' }, 400);
  }

  const body = new URLSearchParams({
    title: params.title || '丫丫计时器',
    desp: params.msg || '',
  }).toString();

  const resp = await fetch(`https://sctapi.ftqq.com/${key}.send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body,
  });

  const data = await resp.json();
  return json(data, resp.status);
}

/** Qmsg酱 QQ 推送 */
async function handleQmsg(params) {
  const key = params.key || '';
  if (!key) {
    return json({ success: false, reason: 'Key 不能为空' }, 400);
  }

  const body = JSON.stringify({ msg: params.msg || '' });

  const resp = await fetch(`https://qmsg.zendee.cn/jsend/${key}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
  });

  const data = await resp.json();
  return json(data, resp.status);
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}
