<script>
  import { createEventDispatcher, onMount, onDestroy } from 'svelte';
  import { fetchArticlesByFeed, fetchFeedById } from './api';
  
  export let feedId = null;
  export let allArticles = [];
  
  const dispatch = createEventDispatcher();
  let articles = [];
  let feed = null;
  let loading = true;
  let error = null;
  let selectedArticleId = null;
  let articleListContainer;
  let scrollStep = 10; // pixels per frame
  let animationFrameId = null;
  let pauseByUser = false;
  let pauseTimeout = null;
  
  $: if (feedId) {
    loadArticles(feedId);
  }
  
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
  
  function selectArticle(articleId) {
    selectedArticleId = articleId;
    const article = (feedId ? articles : allArticles).find(a => a.id === articleId);
    dispatch('select', { article });
  }
  
  function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  }

  function smoothAutoScroll() {
    if (!articleListContainer) {
      animationFrameId = requestAnimationFrame(smoothAutoScroll);
      return;
    }
    if (!pauseByUser) {
      if (
        articleListContainer.scrollTop + articleListContainer.clientHeight >=
        articleListContainer.scrollHeight - 1
      ) {
        articleListContainer.scrollTop = 0;
      } else {
        articleListContainer.scrollTop += scrollStep;
      }
    }
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
  }

  function startAutoScroll() {
    if (animationFrameId) return;
    animationFrameId = requestAnimationFrame(smoothAutoScroll);
  }

  function stopAutoScroll() {
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  function handleMouseEnter() {
    stopAutoScroll();
  }
  function handleMouseLeave() {
    pauseByUser = false;
    startAutoScroll();
  }
  function handleUserScroll() {
    pauseByUser = true;
    stopAutoScroll();
    if (pauseTimeout) clearTimeout(pauseTimeout);
    pauseTimeout = setTimeout(() => {
      pauseByUser = false;
      startAutoScroll();
    }, 2000); // after user scroll, 2 seconds to resume auto scroll
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
            class="article-item {selectedArticleId === article.id ? 'selected' : ''}"
            on:click={() => selectArticle(article.id)}
          >
            <div class="article-title-row">
              <h3 class="article-title">{article.title}</h3>
              <span class="article-date">{formatDate(article.published_at)}</span>
            </div>
            {#if article.summary}
              <p class="article-summary">{article.summary}</p>
            {/if}
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
            class="article-item {selectedArticleId === article.id ? 'selected' : ''}"
            on:click={() => selectArticle(article.id)}
          >
            <div class="article-title-row">
              <h3 class="article-title">{article.title}</h3>
              <span class="article-date">{formatDate(article.published_at)}</span>
            </div>
            {#if article.summary}
              <p class="article-summary">{article.summary}</p>
            {/if}
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
</style> 