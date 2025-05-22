<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { fetchArticlesByFeed, fetchFeedById, fetchArticlesByCategory } from './api';
  
  export let feedId = null;
  export let categoryId = null; // New prop for category filtering
  export let allArticles = [];
  export let paused = false;
  export let selectedArticle = null;
  export let feedMap = {};
  export let enableAutoScroll = true; // 默认开启自动滚动
  
  const dispatch = createEventDispatcher();
  let articles = [];
  let feed = null;
  let loading = true;
  let error = null;
  let selectedArticleId = null;
  let articleListContainer;
  let scrollSpeed = 2000; // 增加滚动速度，从800改为2000 pixels per second
  let lastTimestamp = null;
  let animationFrameId = null;
  let pauseByUser = false;
  let pauseTimeout = null;
  let hoveredArticleId = null;
  
  // 跟踪上一次的feedId和categoryId以检测变化
  let prevFeedId = null;
  let prevCategoryId = null;
  
  // 监听feedId变化
  $: if (feedId !== prevFeedId) {
    console.log(`Feed ID changed from ${prevFeedId} to ${feedId}`);
    prevFeedId = feedId;
    if (feedId) {
      console.log(`Loading articles for feed ID: ${feedId}`);
      loadArticles(feedId);
    }
  }
  
  // 监听categoryId变化
  $: if (categoryId !== prevCategoryId) {
    console.log(`Category ID changed from ${prevCategoryId} to ${categoryId}`);
    prevCategoryId = categoryId;
    if (categoryId) {
      console.log(`Loading articles for category ID: ${categoryId}`);
      loadArticlesByCategory(categoryId);
    }
  }
  
  // 当文章列表变化时检查并确保自动滚动正在运行
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
      
      // 停止当前的自动滚动
      stopAutoScroll();
      
      // load feed info
      feed = await fetchFeedById(id);
      
      // load articles list
      articles = await fetchArticlesByFeed(id);
      
      console.log(`Loaded ${articles.length} articles for feed ${id}`);
      // After loading, make sure auto-scroll is reset and working
      resetScrollPosition();
      // 确保重新启动自动滚动
      ensureAutoScrollActive();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }

  // New function to load articles by category
  async function loadArticlesByCategory(id) {
    if (!id) return;
    
    try {
      loading = true;
      error = null;
      selectedArticleId = null;
      
      // 停止当前的自动滚动
      stopAutoScroll();
      
      // Load articles for this category - will return empty array on error
      articles = await fetchArticlesByCategory(id);
      
      console.log(`Loaded ${articles.length} articles for category ${id}`);
      // After loading, make sure auto-scroll is reset and working
      resetScrollPosition();
      // 确保重新启动自动滚动
      ensureAutoScrollActive();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  // 确保自动滚动处于活动状态
  function ensureAutoScrollActive() {
    if (!enableAutoScroll) return;
    
    console.log('Ensuring auto-scroll is active');
    // 如果没有活动的动画帧，启动一个
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
      
      // 重置lastTimestamp，避免大跳跃
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
    // 确保我们有容器和文章
    if (!articleListContainer || (articles.length === 0 && allArticles.length === 0)) {
      console.log('等待容器或文章加载完成，请求下一帧');
      animationFrameId = requestAnimationFrame(smoothAutoScroll);
      return;
    }
    
    // 仅在未被用户暂停且外部暂停标志未设置时滚动
    if (!pauseByUser && !paused) {
      // 检查是否已滚动到底部
      const isAtBottom = 
        articleListContainer.scrollTop + articleListContainer.clientHeight >=
        articleListContainer.scrollHeight - 5; // 使用5像素的阈值
      
      if (isAtBottom) {
        // 尝试加载更多文章
        const hasLoadedAllArticles = !dispatch('loadMore');
        
        if (hasLoadedAllArticles) {
          // 如果已加载所有文章且已到达底部，则重置到顶部
          console.log('已查看所有文章，重置到顶部');
          articleListContainer.scrollTop = 0;
          // 重置时间戳，以避免下一帧的大跳跃
          lastTimestamp = null;
        }
      } else {
        // 平滑滚动
        if (lastTimestamp !== null) {
          const delta = (timestamp - lastTimestamp) / 1000; // 转换为秒
          const scrollAmount = scrollSpeed * delta;
          
          // 只有当滚动量合理时才滚动（防止浏览器切换标签页后的大跳跃）
          if (scrollAmount > 0 && scrollAmount < 100) {
            articleListContainer.scrollTop += scrollAmount;
          } else {
            console.log('滚动量异常，跳过此帧', scrollAmount);
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
    
    // 设置一个定期检查，确保自动滚动保持活动状态
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
  
  // 当组件更新时，确保自动滚动正在运行
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
        <p>暂无文章</p>
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
    {#if loading}
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
</style> 