<script>
  import { createEventDispatcher } from 'svelte';
  import { fetchArticlesByFeed, fetchFeedById, fetchArticlesByCategory } from './api';
  
  export let feedId = null;
  export let categoryId = null; // New prop for category filtering
  export let allArticles = [];
  export let paused = false;
  export let selectedArticle = null;
  export let feedMap = {};
  
  const dispatch = createEventDispatcher();
  let articles = [];
  let feed = null;
  let loading = true;
  let error = null;
  let selectedArticleId = null;
  let articleListContainer;
  
  // track previous feedId and categoryId to detect changes
  let prevFeedId = null;
  let prevCategoryId = null;
  
  // pagination for category articles
  let categoryPage = 0;
  let hasMoreCategoryArticles = true;
  let categoryLoading = false;
  
  // pagination for feed articles  
  let feedPage = 0;
  let hasMoreFeedArticles = true;
  let feedLoading = false;
  
  // track previous feedId and categoryId to detect changes
  $: if (feedId !== prevFeedId) {
    console.log(`Feed ID changed from ${prevFeedId} to ${feedId}`);
    prevFeedId = feedId;
    if (feedId) {
      console.log(`Loading articles for feed ID: ${feedId}`);
      // Reset pagination when feed changes
      articles = [];
      loadArticlesByFeed(feedId);
    }
  }
  
  // track previous categoryId to detect changes
  $: if (categoryId !== prevCategoryId) {
    console.log(`Category ID changed from ${prevCategoryId} to ${categoryId}`);
    prevCategoryId = categoryId;
    if (categoryId) {
      console.log(`Loading articles for category ID: ${categoryId}`);
      // Reset pagination when category changes
      categoryPage = 0;
      hasMoreCategoryArticles = true;
      articles = [];
      loadArticlesByCategory(categoryId);
    }
  }
  
  // Use a simple approach for selectedArticleId
  $: selectedArticleId = selectedArticle ? selectedArticle.id : null;
  
  // Handle scroll to bottom for loading more articles
  function handleScroll(event) {
    const container = event.target;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight;
    const clientHeight = container.clientHeight;
    const scrollBottom = scrollHeight - scrollTop - clientHeight;
    
    console.log(`Scroll event - feedId: ${feedId}, categoryId: ${categoryId}`);
    
    // Handle category scroll loading
    if (categoryId && hasMoreCategoryArticles && !categoryLoading && scrollBottom <= 50) {
      console.log('Loading more category articles...');
      loadArticlesByCategory(categoryId, true);
      return;
    }
    
    // Handle feed scroll loading
    if (feedId && hasMoreFeedArticles && !feedLoading && scrollBottom <= 50) {
      console.log('Loading more feed articles...');
      loadArticlesByFeed(feedId, true);
      return;
    }
    
    // Handle all articles scroll loading (when neither feedId nor categoryId)
    if (!feedId && !categoryId && scrollBottom <= 50) {
      console.log('All articles scroll - dispatching loadMore event');
      dispatch('loadMore');
    }
  }


  // Load articles by feed with pagination support
  async function loadArticlesByFeed(id, loadMore = false) {
    if (!id || (loadMore && (!hasMoreFeedArticles || feedLoading))) return;
    
    try {
      feedLoading = true;
      if (!loadMore) {
        loading = true;
        error = null;
        selectedArticleId = null;
        feedPage = 0;
        hasMoreFeedArticles = true;
        
        // Load feed info
        try {
          feed = await fetchFeedById(id);
        } catch (err) {
          console.warn('Failed to load feed info:', err);
        }
      }
      
      const PAGE_SIZE = 100;
      const skip = feedPage * PAGE_SIZE;
      
      console.log(`Loading feed articles with skip=${skip}, limit=${PAGE_SIZE}`);
      
      // Use the updated API function with pagination
      const newArticles = await fetchArticlesByFeed(id, skip, PAGE_SIZE);
      
      console.log(`Loaded ${newArticles.length} articles for feed ${id}`);
      
      // Check if we have more articles to load
      if (newArticles.length < PAGE_SIZE) {
        hasMoreFeedArticles = false;
      }
      
      // Update articles and page
      if (loadMore) {
        articles = [...articles, ...newArticles];
      } else {
        articles = newArticles;
        // Reset scroll position to top for new feed
        if (articleListContainer) {
          articleListContainer.scrollTop = 0;
        }
      }
      
      feedPage++;
      
      return newArticles.length > 0;
    } catch (err) {
      error = err.message;
      return false;
    } finally {
      feedLoading = false;
      if (!loadMore) {
        loading = false;
      }
    }
  }

  // Load articles by category with pagination support
  async function loadArticlesByCategory(id, loadMore = false) {
    if (!id || (loadMore && (!hasMoreCategoryArticles || categoryLoading))) return;
    
    try {
      categoryLoading = true;
      if (!loadMore) {
        loading = true;
        error = null;
        selectedArticleId = null;
        categoryPage = 0;
        hasMoreCategoryArticles = true;
      }
      
      const PAGE_SIZE = 100;
      const skip = categoryPage * PAGE_SIZE;
      
      console.log(`Loading category articles with skip=${skip}, limit=${PAGE_SIZE}`);
      
      // Load articles for this category with pagination
      const newArticles = await fetchArticlesByCategory(id, skip, PAGE_SIZE);
      
      console.log(`Loaded ${newArticles.length} articles for category ${id}`);
      
      // Check if we have more articles to load
      if (newArticles.length < PAGE_SIZE) {
        hasMoreCategoryArticles = false;
      }
      
      // Update articles and page
      if (loadMore) {
        articles = [...articles, ...newArticles];
      } else {
        articles = newArticles;
        // Reset scroll position to top for new category
        if (articleListContainer) {
          articleListContainer.scrollTop = 0;
        }
      }
      
      categoryPage++;
      
      return newArticles.length > 0;
    } catch (err) {
      error = err.message;
      return false;
    } finally {
      categoryLoading = false;
    }
  }
  
  async function updateArticleReadStatus(articleId) {
    try {
      const response = await fetch(`/rss-articles/${articleId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          manual_labels: {
            read: true
          }
        })
      });
      if (!response.ok) {
        console.error('Failed to update article read status');
      } else {
        // Update the article in both lists immediately
        const article = (feedId || categoryId ? articles : allArticles).find(a => a.id === articleId);
        if (article) {
          // Create a new object to trigger reactivity
          const updatedArticle = {
            ...article,
            manual_labels: {
              ...article.manual_labels,
              read: true
            }
          };
          
          if (feedId || categoryId) {
            articles = articles.map(a => a.id === articleId ? updatedArticle : a);
          } else {
            allArticles = allArticles.map(a => a.id === articleId ? updatedArticle : a);
          }
        }
      }
    } catch (err) {
      console.error('Error updating article read status:', err);
    }
  }
  
  function isArticleRead(article) {
    return article.manual_labels?.read === true;
  }

  function selectArticle(articleId) {
    const article = (feedId || categoryId ? articles : allArticles).find(a => a.id === articleId);
    if (article && !isArticleRead(article)) {
      updateArticleReadStatus(articleId);
    }
    dispatch('select', { article });
  }
  
  function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  }
</script>

<div class="article-container">
  {#if feedId === null && categoryId === null}
    {#if allArticles.length === 0}
      <div class="empty">
        <p>No articles yet</p>
      </div>
    {:else}
      <div
        class="articles-list"
        bind:this={articleListContainer}
        tabindex="0"
        style="outline: none;"
        on:scroll={handleScroll}
      >
        {#each allArticles as article (article.id)}
          <div 
            class="article-item {selectedArticleId === article.id ? 'selected' : ''} {isArticleRead(article) ? 'read' : ''}"
            on:click={() => selectArticle(article.id)}
          >
            <div class="article-title-row">
              <h3 class="article-title">{article.title}</h3>
              {#if isArticleRead(article)}
                <span class="read-badge">Read</span>
              {/if}
              {#if feedMap && article.feed_id}
                <span class="article-feed">{feedMap[article.feed_id]}</span>
              {/if}
              <span class="article-date">{formatDate(article.published_at)}</span>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  {:else}
    {#if loading && articles.length === 0}
      <div class="loading">Loading articles...</div>
    {:else if error}
      <div class="error">
        <p>{error}</p>
        <button on:click={() => feedId ? loadArticlesByFeed(feedId) : loadArticlesByCategory(categoryId)}>Retry</button>
      </div>
    {:else if articles.length === 0}
      <div class="empty">
        <p>No articles in this {feedId ? 'feed' : 'category'}</p>
      </div>
    {:else}
      <div
        class="articles-list"
        bind:this={articleListContainer}
        tabindex="0"
        style="outline: none;"
        on:scroll={handleScroll}
      >
        {#each articles as article (article.id)}
          <div 
            class="article-item {selectedArticleId === article.id ? 'selected' : ''} {isArticleRead(article) ? 'read' : ''}"
            on:click={() => selectArticle(article.id)}
          >
            <div class="article-title-row">
              <h3 class="article-title">{article.title}</h3>
              {#if isArticleRead(article)}
                <span class="read-badge">Read</span>
              {/if}
              {#if feedMap && article.feed_id}
                <span class="article-feed">{feedMap[article.feed_id]}</span>
              {/if}
              <span class="article-date">{formatDate(article.published_at)}</span>
            </div>
          </div>
        {/each}
        {#if (categoryLoading && categoryPage > 0) || (feedLoading && feedPage > 0)}
          <div class="loading-more">Loading more articles...</div>
        {/if}
        {#if categoryId && hasMoreCategoryArticles && !categoryLoading}
          <div class="load-more-section">
            <button class="load-more-btn" on:click={() => loadArticlesByCategory(categoryId, true)}>
              Load More Articles
            </button>
            <div class="debug-info">
              <small>Debug: categoryId={categoryId}, hasMore={hasMoreCategoryArticles}, page={categoryPage}</small>
            </div>
          </div>
        {/if}
        {#if feedId && hasMoreFeedArticles && !feedLoading}
          <div class="load-more-section">
            <button class="load-more-btn" on:click={() => loadArticlesByFeed(feedId, true)}>
              Load More Articles
            </button>
            <div class="debug-info">
              <small>Debug: feedId={feedId}, hasMore={hasMoreFeedArticles}, page={feedPage}</small>
            </div>
          </div>
        {/if}
      </div>
    {/if}
  {/if}
</div>

<style>
  :root {
    --color-surface: #f7fafd;
    --color-border: #e0e6ed;
    --color-brand: linear-gradient(90deg, #4f8cff 0%, #38c6ff 100%);
    --color-brand-hover: #357ae8;
    --color-text-primary: #222c3c;
    --color-text-secondary: #7b8a9c;
    --shadow-elevation-1: 0 2px 8px rgba(80, 120, 200, 0.08);
    --shadow-elevation-2: 0 4px 16px rgba(80, 120, 200, 0.12);
    --radius: 12px;
    --font-size-lg: 1rem;
    --font-size-sm: 1rem;
    --font-family: 'Segoe UI', 'PingFang SC', 'Hiragino Sans', Arial, sans-serif;
  }

  .article-container {
    padding: 1.2rem 1.2rem 1.2rem 1.2rem;
    background: var(--color-surface);
    font-family: var(--font-family);
  }
  
  .feed-header {
    margin-bottom: 1.2rem;
    padding-bottom: 0.7rem;
    border-bottom: 1.5px solid var(--color-border);
  }
  .feed-header h2 {
    margin: 0 0 0.5rem 0;
    font-size: 1.3rem;
    color: var(--color-text-primary);
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .feed-description {
    color: var(--color-text-secondary);
    font-size: 0.98rem;
    margin: 0;
  }
  .articles-list {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    max-height: 80vh;
    overflow-y: auto;
  }
  .article-item {
    padding: 0.3rem 0.7rem;
    background: #fff;
    border-radius: var(--radius);
    box-shadow: var(--shadow-elevation-1);
    border: 1.5px solid transparent;
    cursor: pointer;
    transition: box-shadow 0.18s, border 0.18s, background 0.18s, transform 0.12s;
    margin-bottom: 0;
    position: relative;
    display: flex;
    flex-direction: column;
  }
  .article-item:hover {
    box-shadow: var(--shadow-elevation-2);
    background: #f0f7ff;
    transform: translateY(-2px) scale(1.02);
  }
  .article-item.selected {
    background: linear-gradient(90deg, #e3f0ff 60%, #f7fafd 100%);
    border-left: 4px solid #4f8cff;
    border-color: #4f8cff;
    box-shadow: 0 4px 16px rgba(80, 120, 200, 0.16);
  }
  .article-item.read {
    background: #f0f0f0;
    opacity: 0.85;
  }
  .article-item.read:hover {
    background: #e8e8e8;
  }
  .article-item.read .article-title {
    color: #666;
  }
  .read-badge {
    background: #4CAF50;
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 0.7em;
    margin-right: 8px;
  }
  .article-title-row {
    display: flex;
    align-items: center;
    gap: 0.5em;
    margin-bottom: 0;
    justify-content: flex-start;
    min-width: 0;
  }
  .article-title {
    margin: 0;
    font-size: var(--font-size-lg);
    font-weight: 600;
    color: var(--color-text-primary);
    letter-spacing: 0.2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 0 1 auto;
    min-width: 0;
  }
  .article-date {
    color: var(--color-text-secondary);
    font-size: 0.75em;
    margin-left: 0.5em;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .article-feed {
    color: var(--color-text-secondary);
    font-size: 0.7em;
    background: var(--color-border);
    padding: 2px 6px;
    border-radius: 4px;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .article-summary {
    margin: 0;
    color: #333;
    font-size: var(--font-size-sm);
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .loading, .error, .empty {
    padding: 2.2rem 0.5rem;
    text-align: center;
    color: var(--color-text-secondary);
    font-size: var(--font-size-lg);
    border-radius: var(--radius);
    background: #fff;
    box-shadow: var(--shadow-elevation-1);
    margin: 1.5rem 0.5rem;
  }
  .error button {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    background: var(--color-brand);
    color: white;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: var(--font-size-sm);
  }
  .error button:hover {
    background: var(--color-brand-hover);
  }
  .loading-more {
    text-align: center;
    padding: 1rem;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }
  
  .load-more-section {
    text-align: center;
    padding: 1rem;
    border-top: 1px solid var(--color-border);
    margin-top: 0.5rem;
  }
  
  .load-more-btn {
    background: var(--color-brand);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: var(--radius);
    cursor: pointer;
    font-size: 0.9rem;
    transition: background 0.2s;
  }
  
  .load-more-btn:hover {
    background: var(--color-brand-hover);
  }
  
  .debug-info {
    margin-top: 0.5rem;
    color: var(--color-text-secondary);
  }
</style> 