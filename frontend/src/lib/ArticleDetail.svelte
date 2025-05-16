<script>
  import { fetchArticleById } from './api';
  import { createEventDispatcher } from 'svelte';
  
  export let article = null;
  
  let fullArticle = null;
  let loading = false;
  let error = null;
  
  const dispatch = createEventDispatcher();
  
  $: if (article && article.id) {
    loadFullArticle(article.id);
  } else {
    fullArticle = null;
  }
  
  async function loadFullArticle(articleId) {
    if (!articleId) return;
    
    try {
      loading = true;
      error = null;
      fullArticle = await fetchArticleById(articleId);
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleString('zh-CN');
  }
</script>

<div class="article-detail">
  {#if article}
    <button class="close-btn" on:click={() => dispatch('close')} title="Close">×</button>
    {#if loading}
      <div class="loading">加载文章内容中...</div>
    {:else if error}
      <div class="error">
        <p>{error}</p>
        <button on:click={() => loadFullArticle(article.id)}>重试</button>
      </div>
    {:else if fullArticle}
      <div class="article-header">
        <h1>{fullArticle.title}</h1>
        <div class="article-meta">
          <span class="article-date">{formatDate(fullArticle.published_at)}</span>
          {#if fullArticle.author}
            <span class="article-author">作者: {fullArticle.author}</span>
          {/if}
        </div>
        {#if fullArticle.link}
          <a href={fullArticle.link} target="_blank" rel="noopener noreferrer" class="article-link">
            查看原文
          </a>
        {/if}
      </div>
      
      <div class="article-content">
        {#if fullArticle.no_content_reason}
          <p class="empty">{fullArticle.no_content_reason}</p>
        {:else if fullArticle.content}
          {@html fullArticle.content}
        {:else if fullArticle.summary}
          {#if /<|>/.test(fullArticle.summary)}
            {@html fullArticle.summary}
          {:else}
            <p>{fullArticle.summary}</p>
          {/if}
        {:else}
          <p>没有可显示的内容</p>
        {/if}
      </div>
    {/if}
  {:else}
    <div class="empty">
      <p>请选择一篇文章查看详情</p>
    </div>
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
    --radius: 14px;
    --font-size-lg: 1.35rem;
    --font-size-sm: 0.98rem;
    --font-family: 'Segoe UI', 'PingFang SC', 'Hiragino Sans', Arial, sans-serif;
  }

  .article-detail {
    height: 100%;
    overflow-y: auto;
    padding: 2.2rem 2.5rem 2.2rem 2.5rem;
    background: var(--color-surface);
    font-family: var(--font-family);
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
  }
  .article-header {
    width: 100%;
    max-width: 820px;
    margin-bottom: 2.2rem;
    padding-bottom: 1.1rem;
    border-bottom: 1.5px solid var(--color-border);
    background: #fff;
    border-radius: var(--radius) var(--radius) 0 0;
    box-shadow: var(--shadow-elevation-1);
    padding-top: 1.2rem;
    padding-left: 2rem;
    padding-right: 2rem;
  }
  .article-header h1 {
    margin: 0 0 1.1rem 0;
    font-size: 1.7rem;
    line-height: 1.3;
    color: var(--color-text-primary);
    font-weight: 700;
    letter-spacing: 0.5px;
  }
  .article-meta {
    display: flex;
    gap: 1.2rem;
    color: var(--color-text-secondary);
    font-size: 1.01rem;
    margin-bottom: 0.5rem;
  }
  .article-link {
    display: inline-block;
    color: #4f8cff;
    text-decoration: none;
    font-weight: 500;
    margin-top: 0.7rem;
    transition: color 0.18s;
  }
  .article-link:hover {
    text-decoration: underline;
    color: #357ae8;
  }
  .article-content {
    width: 100%;
    max-width: 820px;
    background: #fff;
    border-radius: 0 0 var(--radius) var(--radius);
    box-shadow: var(--shadow-elevation-1);
    font-size: 1.08rem;
    line-height: 1.7;
    color: #333;
    padding: 2rem;
    margin-bottom: 2.5rem;
    min-height: 200px;
    word-break: break-word;
  }
  .article-content img {
    max-width: 100%;
    height: auto;
    margin: 10px 0;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(80, 120, 200, 0.08);
  }
  .loading, .error, .empty {
    padding: 2.2rem 0.5rem;
    text-align: center;
    color: var(--color-text-secondary);
    font-size: 1.08rem;
    border-radius: var(--radius);
    background: #fff;
    box-shadow: var(--shadow-elevation-1);
    margin: 2.5rem 0.5rem;
    width: 100%;
    max-width: 700px;
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
  @media (max-width: 900px) {
    .article-detail {
      padding: 1.2rem 0.5rem;
    }
    .article-header, .article-content {
      padding-left: 1rem;
      padding-right: 1rem;
    }
  }
  @media (max-width: 600px) {
    .article-header, .article-content {
      padding-left: 0.3rem;
      padding-right: 0.3rem;
    }
    .article-detail {
      padding: 0.5rem 0.1rem;
    }
  }
  .close-btn {
    position: absolute;
    top: 1.2rem;
    right: 1.2rem;
    background: transparent;
    border: none;
    font-size: 1.3rem;
    color: #888;
    cursor: pointer;
    z-index: 20;
    transition: color 0.18s, background 0.18s;
    border-radius: 50%;
    width: 1.5rem;
    height: 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    line-height: 1;
    text-align: center;
  }
  .close-btn:hover,
  .close-btn:focus {
    color: #fff;
    background: #dc3545;
    outline: none;
  }
</style> 