// API base URL
const API_BASE_URL = '';  // 使用相对路径，以便与前端服务代理一致

export async function fetchFeeds() {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/`);
  if (!response.ok) {
    throw new Error('Failed to fetch feeds');
  }
  return await response.json();
}

export async function fetchFeedById(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/${feedId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch feed ${feedId}`);
  }
  return await response.json();
}

export async function fetchArticlesByFeed(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-articles/feed/${feedId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch articles for feed ${feedId}`);
  }
  return await response.json();
}

export async function fetchArticlesByCategory(categoryId, skip = 0, limit = 100) {
  console.log(`Fetching articles for category ${categoryId} with skip=${skip}, limit=${limit}`);
  try {
    const response = await fetch(`${API_BASE_URL}/rss-articles?category_id=${categoryId}&skip=${skip}&limit=${limit}`);
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API error: ${errorText}`);
      throw new Error(`Failed to fetch articles for category ${categoryId}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching articles for category ${categoryId}:`, error);
    return []; // Return empty array on error
  }
}

export async function fetchArticleById(articleId) {
  const response = await fetch(`${API_BASE_URL}/rss-articles/${articleId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch article ${articleId}`);
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
    throw new Error('Failed to create feed');
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
    throw new Error(`Failed to update feed ${feedId}`);
  }
  return await response.json();
}

export async function deleteFeed(feedId) {
  const response = await fetch(`${API_BASE_URL}/rss-feeds/${feedId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new Error(`Failed to delete feed ${feedId}`);
  }
  return await response.json();
} 