<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { fetchArticlesByFeed, fetchFeedById, fetchArticlesByCategory } from './api';
  
  export let feedId = null;
  export let categoryId = null; // New prop for category filtering
  export let allArticles = [];
  export let paused = false;
  export let selectedArticle = null;
  export let feedMap = {};
  export let enableAutoScroll = true; // default auto scroll
  
  const dispatch = createEventDispatcher();
  let articles = [];
  let feed = null;
  let loading = true;
  let error = null;
  let selectedArticleId = null;
  let articleListContainer;
  let scrollSpeed = 1000; // pixels per second
  let lastTimestamp = null;
  let animationFrameId = null;
  let pauseByUser = false;
  let pauseTimeout = null;
  let hoveredArticleId = null;
  
  // track previous feedId and categoryId to detect changes
  let prevFeedId = null;
  let prevCategoryId = null;
  
  // pagination for category articles
  let categoryPage = 0;
  let hasMoreCategoryArticles = true;
  let categoryLoading = false;
  
  // track previous feedId and categoryId to detect changes
  $: if (feedId !== prevFeedId) {
    console.log(`Feed ID changed from ${prevFeedId} to ${feedId}`);
    prevFeedId = feedId;
    if (feedId) {
      console.log(`Loading articles for feed ID: ${feedId}`);
      loadArticles(feedId);
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
  
  // when article list changes, check and ensure auto scroll is running
  $: {
    if (articles && articles.length > 0) {
      console.log(`Articles updated, length: ${articles.length}, ensuring auto-scroll is active`);
      ensureAutoScrollActive();
    }
  }
  
  // Use a simple approach for selectedArticleId
  $: selectedArticleId = selectedArticle ? selectedArticle.id : null;
  
  async function loadArticles(id) {
    if (!id) return;
    
    try {
      loading = true;
      error = null;
      selectedArticleId = null;
      
      // stop current auto scroll
      stopAutoScroll();
      
      // load feed info
      feed = await fetchFeedById(id);
      
      // load articles list
      articles = await fetchArticlesByFeed(id);
      
      console.log(`Loaded ${articles.length} articles for feed ${id}`);
      // After loading, make sure auto-scroll is reset and working
      resetScrollPosition();
      // ensure auto scroll is active
      ensureAutoScrollActive();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // Load articles by category with pagination support
  async function loadArticlesByCategory(id, loadMore = false) {
    if (!id || (loadMore && (!hasMoreCategoryArticles || categoryLoading))) return;
    
    try {
      categoryLoading = true;
      if (!loadMore) {
        error = null;
        selectedArticleId = null;
        // stop current auto scroll
        stopAutoScroll();
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
        // After initial loading, make sure auto-scroll is reset and working
        resetScrollPosition();
      }
      
      categoryPage++;
      
      // ensure auto scroll is active
      ensureAutoScrollActive();
      
      return newArticles.length > 0;
    } catch (err) {
      error = err.message;
      return false;
    } finally {
      categoryLoading = false;
    }
  }
  
  // ensure auto scroll is active
  function ensureAutoScrollActive() {
    if (!enableAutoScroll) return;
    
    console.log('Ensuring auto-scroll is active');
    // if no active animation frame, start auto scroll
    if (!animationFrameId) {
      console.log('No active animation frame, starting auto-scroll');
      startAutoScroll();
    } else {
      console.log('Auto-scroll already active');
    }
  }
  
  // Simpler function to just reset scroll position without messing with auto-scroll
  function resetScrollPosition() {
    if (articleListContainer) {
      console.log('Resetting scroll position to top');
      articleListContainer.scrollTop = 0;
      pauseByUser = false; // Reset user pause
      
      // reset lastTimestamp, avoid big jump
      lastTimestamp = null;
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

  function smoothAutoScroll(timestamp) {
    // ensure we have container and articles
    if (!articleListContainer || (articles.length === 0 && allArticles.length === 0)) {
      console.log('waiting for container or articles to load, requesting next frame');
      animationFrameId = requestAnimationFrame(smoothAutoScroll);
      return;
    }
    
    // only scroll if not paused by user and external pause flag is not set
    if (!pauseByUser && !paused) {
      // check if we have scrolled to the bottom
      const isAtBottom = 
        articleListContainer.scrollTop + articleListContainer.clientHeight >=
        articleListContainer.scrollHeight - 5; // use 5 pixels threshold
      
      if (isAtBottom) {
        // try to load more articles
        let hasLoadedAllArticles = true;
        
        if (categoryId) {
          // For category view, use our pagination method
          if (hasMoreCategoryArticles && !categoryLoading) {
            loadArticlesByCategory(categoryId, true);
            hasLoadedAllArticles = false;
          }
        } else {
          // For other views, use the existing loadMore event
          hasLoadedAllArticles = !dispatch('loadMore');
        }
        
        if (hasLoadedAllArticles) {
          // if all articles are loaded and we have scrolled to the bottom, reset to top
          console.log('all articles are loaded, resetting to top');
          articleListContainer.scrollTop = 0;
          // reset timestamp, to avoid big jump in next frame
          lastTimestamp = null;
        }
      } else {
        // smooth scroll
        if (lastTimestamp !== null) {
          const delta = (timestamp - lastTimestamp) / 1000; // convert to seconds
          const scrollAmount = scrollSpeed * delta;
          
          // only scroll if scroll amount is reasonable (prevent big jump when browser switches tabs)
          if (scrollAmount > 0 && scrollAmount < 100) {
            articleListContainer.scrollTop += scrollAmount;
          } else {
            console.log('scroll amount is abnormal, skipping this frame', scrollAmount);
          }
        }
      }
    }
    
    lastTimestamp = timestamp;
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
  }

  function startAutoScroll() {
    if (animationFrameId) {
      console.log('Auto scroll already running, no need to start');
      return;
    }
    console.log('Auto scroll started');
    lastTimestamp = null;
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
  }

  function stopAutoScroll() {
    if (animationFrameId) {
      console.log('Auto scroll stopped');
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    } else {
      console.log('Auto scroll already stopped');
    }
  }

  // These handlers should be effective immediately
  function handleMouseEnter() {
    pauseByUser = true;
    console.log('Mouse entered list - pausing scroll');
  }
  
  function handleMouseLeave() {
    pauseByUser = false;
    console.log('Mouse left list - resuming scroll');
  }

  function handleUserScroll() {
    pauseByUser = true;
    if (pauseTimeout) clearTimeout(pauseTimeout);
    
    pauseTimeout = setTimeout(() => {
      if (!articleListContainer.matches(':hover')) {
        pauseByUser = false;
        console.log('Resuming scroll after user interaction');
      } else {
        console.log('Not resuming scroll - mouse still in list');
      }
    }, 2000); // after user scroll, 2 seconds to resume auto scroll
  }

  function handleMouseEnterItem(articleId) {
    hoveredArticleId = articleId;
  }
  function handleMouseLeaveItem(articleId) {
    if (hoveredArticleId === articleId) {
      hoveredArticleId = null;
    }
  }

  onMount(() => {
    console.log('ArticleList mounted, starting auto-scroll');
    if (enableAutoScroll) {
      startAutoScroll();
    }
    
    // set a periodic check to ensure auto scroll is active
    const autoScrollCheckInterval = setInterval(() => {
      if (enableAutoScroll && !animationFrameId) {
        console.log('Auto-scroll check: Restarting stopped auto-scroll');
        startAutoScroll();
      }
    }, 5000);
    
    return () => {
      stopAutoScroll();
      if (pauseTimeout) clearTimeout(pauseTimeout);
      clearInterval(autoScrollCheckInterval);
    };
  });
  
  // when component updates, ensure auto scroll is running
  onDestroy(() => {
    console.log('ArticleList component being destroyed');
    stopAutoScroll();
    if (pauseTimeout) clearTimeout(pauseTimeout);
  });
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
        on:mouseenter={handleMouseEnter}
        on:mouseleave={handleMouseLeave}
        on:wheel={handleUserScroll}
        on:scroll={handleUserScroll}
        tabindex="0"
        style="outline: none;"
      >
        {#each allArticles as article (article.id)}
          <div 
            class="article-item {(selectedArticleId === article.id || hoveredArticleId === article.id) ? 'selected' : ''} {isArticleRead(article) ? 'read' : ''}"
            on:click={() => selectArticle(article.id)}
            on:mouseenter={() => handleMouseEnterItem(article.id)}
            on:mouseleave={() => handleMouseLeaveItem(article.id)}
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
        <button on:click={() => feedId ? loadArticles(feedId) : loadArticlesByCategory(categoryId)}>Retry</button>
      </div>
    {:else if articles.length === 0}
      <div class="empty">
        <p>No articles in this {feedId ? 'feed' : 'category'}</p>
      </div>
    {:else}
      <div
        class="articles-list"
        bind:this={articleListContainer}
        on:mouseenter={handleMouseEnter}
        on:mouseleave={handleMouseLeave}
        on:wheel={handleUserScroll}
        on:scroll={handleUserScroll}
        tabindex="0"
        style="outline: none;"
      >
        {#each articles as article (article.id)}
          <div 
            class="article-item {(selectedArticleId === article.id || hoveredArticleId === article.id) ? 'selected' : ''} {isArticleRead(article) ? 'read' : ''}"
            on:click={() => selectArticle(article.id)}
            on:mouseenter={() => handleMouseEnterItem(article.id)}
            on:mouseleave={() => handleMouseLeaveItem(article.id)}
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
        {#if categoryLoading && categoryPage > 0}
          <div class="loading-more">Loading more articles...</div>
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
    /* height: 100%; */
    /* overflow-y: auto; */
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
  .error {
    color: #dc3545;
    background: #fff0f2;
  }
  .empty {
    color: var(--color-text-secondary);
    background: #f8fafc;
  }
  button {
    font-size: var(--font-size-sm);
    padding: 0.4rem 1.1rem;
    background: var(--color-brand);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    cursor: pointer;
    box-shadow: var(--shadow-elevation-1);
    transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
    font-weight: 500;
    outline: none;
    margin-top: 0.7rem;
  }
  button:hover,
  button:focus {
    background: var(--color-brand-hover);
    box-shadow: var(--shadow-elevation-2);
    transform: translateY(-2px) scale(1.04);
  }
  @media (max-width: 700px) {
    .article-container {
      padding: 0.7rem 0.3rem;
    }
    .feed-header {
      margin-bottom: 0.7rem;
      padding-bottom: 0.3rem;
    }
  }
  body {
    font-size: 11px;
  }
  .article-feed {
    color: var(--color-text-secondary);
    font-size: 0.85em;
    margin: 0 0.7em;
    font-style: italic;
    white-space: nowrap;
  }
  .loading-more {
    padding: 1rem;
    text-align: center;
    color: var(--color-text-secondary);
    font-style: italic;
  }
</style> 