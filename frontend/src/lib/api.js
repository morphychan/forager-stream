// API服务，处理与后端的通信
const API_BASE_URL = 'http://192.168.41.31:8000';

export async function fetchFeeds() {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/`);
  if (!response.ok) {
    throw new Error('获取RSS订阅源失败');
  }
  return await response.json();
}

export async function fetchFeedById(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/${feedId}`);
  if (!response.ok) {
    throw new Error(`获取RSS订阅源 ${feedId} 失败`);
  }
  return await response.json();
}

export async function fetchArticlesByFeed(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-articles/feed/${feedId}`);
  if (!response.ok) {
    throw new Error(`获取订阅源 ${feedId} 的文章失败`);
  }
  return await response.json();
}

export async function fetchArticleById(articleId) {
  const response = await fetch(`${API_BASE_URL}/rss-articles/${articleId}`);
  if (!response.ok) {
    throw new Error(`获取文章 ${articleId} 失败`);
  }
  return await response.json();
}

export async function createFeed(feedData) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedData),
  });
  if (!response.ok) {
    throw new Error('创建RSS订阅源失败');
  }
  return await response.json();
}

export async function updateFeed(feedId, feedData) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/${feedId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedData),
  });
  if (!response.ok) {
    throw new Error(`更新RSS订阅源 ${feedId} 失败`);
  }
  return await response.json();
}

export async function deleteFeed(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/${feedId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`删除RSS订阅源 ${feedId} 失败`);
  }
  return await response.json();
} 