<script>
  import FeedList from './lib/FeedList.svelte';
  import ArticleList from './lib/ArticleList.svelte';
  import ArticleDetail from './lib/ArticleDetail.svelte';
  import HeadlineMarquee from './lib/HeadlineMarquee.svelte';
  import { fetchArticlesByFeed, fetchFeeds } from './lib/api';
  
  let selectedFeedId = null;
  let selectedArticle = null;
  let allArticles = [];

  async function loadAllArticles() {
    let feeds = await fetchFeeds();
    if (!Array.isArray(feeds)) feeds = [];
    let articles = [];
    for (const feed of feeds) {
      let feedArticles = await fetchArticlesByFeed(feed.id);
      if (!Array.isArray(feedArticles)) feedArticles = [];
      articles.push(...feedArticles);
    }
    // 过滤掉没有 id、title、published_at 的脏数据
    articles = articles.filter(a => a && a.id && a.title && a.published_at);
    // 按时间新到旧排序
    allArticles = articles.sort((a, b) => new Date(b.published_at) - new Date(a.published_at));
    // 调试输出
    console.log('feeds:', feeds);
    console.log('allArticles:', allArticles);
  }

  loadAllArticles();

  function handleFeedSelect(event) {
    selectedFeedId = event.detail.feedId;
    selectedArticle = null;
  }
  
  function handleArticleSelect(event) {
    selectedArticle = event.detail.article;
  }
</script>

<main>
  <HeadlineMarquee articles={allArticles} />
  <div class="app-header">
    <h1>RSS 阅读器</h1>
  </div>
  
  <div class="app-container">
    <div class="sidebar">
      <FeedList on:select={handleFeedSelect} />
    </div>
    
    <div class="content">
      <div class="article-list-section">
        <ArticleList feedId={selectedFeedId} on:select={handleArticleSelect} />
      </div>
      
      <div class="article-detail-section">
        <ArticleDetail article={selectedArticle} />
      </div>
    </div>
  </div>
</main>

<style>
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
    margin: 0;
    padding: 0;
    background-color: #f8f9fa;
    color: #212529;
  }
  
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
    max-width: 100%;
    margin: 0 auto;
  }
  
  .app-header {
    background-color: #007bff;
    color: white;
    padding: 0.5rem 1rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }
  
  .app-header h1 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .app-container {
    display: flex;
    flex: 1;
    overflow: hidden;
  }
  
  .sidebar {
    width: 250px;
    background-color: white;
    border-right: 1px solid #dee2e6;
    height: 100%;
    overflow-y: auto;
  }
  
  .content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }
  
  .article-list-section {
    width: 350px;
    border-right: 1px solid #dee2e6;
    background-color: white;
    height: 100%;
    overflow-y: auto;
  }
  
  .article-detail-section {
    flex: 1;
    background-color: white;
    height: 100%;
    overflow-y: auto;
  }
  
  @media (max-width: 1024px) {
    .app-container {
      flex-direction: column;
    }
    
    .sidebar {
      width: 100%;
      height: auto;
      max-height: 200px;
    }
    
    .content {
      flex-direction: column;
    }
    
    .article-list-section {
      width: 100%;
      height: auto;
      max-height: 300px;
    }
  }
</style>
