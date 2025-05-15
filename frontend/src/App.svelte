<script>
  import { onMount } from 'svelte';
  import FeedList from './lib/FeedList.svelte';
  import ArticleList from './lib/ArticleList.svelte';
  import ArticleDetail from './lib/ArticleDetail.svelte';
  import HeadlineMarquee from './lib/HeadlineMarquee.svelte';

  let selectedFeedId = null;
  let selectedArticle = null;
  let rawArticles = [];
  let loading = false;
  let error = null;

  async function loadAllArticles() {
    loading = true;
    error = null;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    try {
      const res = await fetch('/rss-articles', { signal: controller.signal });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const text = await res.text();
      console.log('response api text:', text);
      try {
        rawArticles = JSON.parse(text);
      } catch {
        throw new Error('Invalid JSON response');
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        error = 'Request timed out, please try again later';
      } else {
        error = e.message;
      }
    } finally {
      loading = false;
      clearTimeout(timeoutId);
    }
  }

  onMount(loadAllArticles);

  $: allArticles = rawArticles
    .filter(a => a?.id && a.title && a.published_at)
    .sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

  function handleFeedSelect(event) {
    selectedFeedId = event.detail.feedId;
    selectedArticle = null;
  }

  function handleArticleSelect(event) {
    selectedArticle = event.detail.article;
  }
</script>

<main>
  <header class="header">
    <h1>RSS Reader</h1>
  </header>

  <section class="marquee-container">
    {#if loading}
      <div class="skeleton-marquee"></div>
    {:else}
      {#if error}
        <div class="marquee-error">Marquee load error: {error}</div>
      {/if}
      <HeadlineMarquee articles={allArticles} />
    {/if}
  </section>

  <div class="layout">
    <aside class="sidebar">
      <FeedList on:select={handleFeedSelect} />
    </aside>
    <section class="main-content">
      <div class="article-list">
        <ArticleList
          feedId={selectedFeedId}
          on:select={handleArticleSelect}
        />
      </div>
      <div class="article-detail">
        <ArticleDetail article={selectedArticle} />
      </div>
    </section>
  </div>
</main>

<style>
  :root {
    --color-bg: #fafafa;
    --color-surface: #ffffff;
    --color-primary: #4a90e2;
    --color-on-primary: #ffffff;
    --color-text: #333333;
    --color-muted: #777777;
    --color-border: #e0e0e0;
    --radius: 8px;
    --spacing: 16px;
  }

  :global(body) {
    margin: 0;
    font-family: "Helvetica Neue", Arial, sans-serif;
    background: var(--color-bg);
    color: var(--color-text);
  }

  main { display: flex; flex-direction: column; height: 100vh; }
  .header {
    position: sticky; top: 0;
    background: var(--color-surface);
    padding: var(--spacing);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    z-index: 10;
  }
  .header h1 { margin: 0; color: var(--color-primary); font-size: 1.75rem; }

  .marquee-container {
    position: sticky; top: 64px;
    background: var(--color-surface);
    padding: var(--spacing);
    border-bottom: 1px solid var(--color-border);
    z-index: 9;
  }
  .marquee-error {
    color: #d32f2f;
    margin-bottom: var(--spacing);
    text-align: center;
  }

  .layout { flex: 1; display: flex; overflow: hidden; }
  .sidebar {
    width: 260px;
    background: var(--color-surface);
    border-right: 1px solid var(--color-border);
    padding: var(--spacing);
    overflow-y: auto;
  }
  .main-content { flex: 1; display: flex; overflow: hidden; }

  .article-list,
  .article-detail {
    background: var(--color-surface);
    margin: var(--spacing);
    border-radius: var(--radius);
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    overflow-y: auto;
  }
  .article-list { width: 320px; padding: var(--spacing); }
  .article-detail { flex: 1; padding: var(--spacing); }

  .skeleton-marquee {
    height: 2rem;
    background: var(--color-border);
    border-radius: var(--radius);
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse { 0%{opacity:1;}50%{opacity:0.4;}100%{opacity:1;} }

  @media (max-width: 1024px) {
    .layout { flex-direction: column; }
    .sidebar { width: 100%; max-height: 200px; }
    .main-content { flex-direction: column; }
    .article-list { width: 100%; max-height: 300px; }
    .article-detail { margin: var(--spacing) 0; }
  }
</style>
