<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { fetchArticlesByFeed, fetchFeedById } from './api';
  
  export let feedId = null;
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
  let scrollSpeed = 600; // pixels per second
  let lastTimestamp = null;
  let animationFrameId = null;
  let pauseByUser = false;
  let pauseTimeout = null;
  let hoveredArticleId = null;
  
  $: if (feedId) {
    loadArticles(feedId);
  }
  
  $: selectedArticleId = selectedArticle?.id || null;
  
  async function loadArticles(id) {
    if (!id) return;
    
    try {
      loading = true;
      error = null;
      selectedArticleId = null;
      
      // load feed info
      feed = await fetchFeedById(id);
      
      // load articles list
      articles = await fetchArticlesByFeed(id);
      
      // no auto select first article
      // if (articles.length > 0) {
      //   selectArticle(articles[0].id);
      // }
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
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
        const article = (feedId ? articles : allArticles).find(a => a.id === articleId);
        if (article) {
          // Create a new object to trigger reactivity
          const updatedArticle = {
            ...article,
            manual_labels: {
              ...article.manual_labels,
              read: true
            }
          };
          
          if (feedId) {
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
    const article = (feedId ? articles : allArticles).find(a => a.id === articleId);
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
    if (!articleListContainer) {
      animationFrameId = requestAnimationFrame(smoothAutoScroll);
      return;
    }
    
    // Only scroll if not paused by user interaction or external pause flag
    if (!pauseByUser && !paused) {
      if (
        articleListContainer.scrollTop + articleListContainer.clientHeight >=
        articleListContainer.scrollHeight - 1
      ) {
        // Check if we're at the end of all articles
        const hasLoadedAllArticles = !dispatch('loadMore');
        
        // Only reset to top if we've loaded all articles AND reached the bottom
        if (hasLoadedAllArticles) {
          console.log('All articles viewed, resetting to top');
          articleListContainer.scrollTop = 0;
        }
        // Otherwise, don't reset and let new content load and continue scrolling
      } else {
        if (lastTimestamp !== null) {
          const delta = (timestamp - lastTimestamp) / 1000; // 秒
          articleListContainer.scrollTop += scrollSpeed * delta;
        }
      }
    }
    
    lastTimestamp = timestamp;
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
  }

  function startAutoScroll() {
    if (animationFrameId) return;
    lastTimestamp = null;
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
    console.log('Auto scroll started');
  }

  function stopAutoScroll() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  // These handlers should be effective immediately
  function handleMouseEnter() {
    pauseByUser = true;
    // For debugging
    console.log('Mouse entered list - pausing scroll');
  }
  
  function handleMouseLeave() {
    pauseByUser = false;
    // For debugging
    console.log('Mouse left list - resuming scroll');
  }

  function handleUserScroll() {
    pauseByUser = true;
    // 不停止自动滚动，只是暂停
    // stopAutoScroll();
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
    startAutoScroll();
    return () => {
      stopAutoScroll();
      if (pauseTimeout) clearTimeout(pauseTimeout);
    };
  });
</script>

<div class="article-container">
  {#if feedId === null}
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
        <button on:click={() => loadArticles(feedId)}>Retry</button>
      </div>
    {:else if articles.length === 0}
      <div class="empty">
        <p>No articles in this feed</p>
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