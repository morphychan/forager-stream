<script>
  import { onMount } from 'svelte';
  import FeedList from './lib/FeedList.svelte';
  import ArticleList from './lib/ArticleList.svelte';
  import ArticleDetail from './lib/ArticleDetail.svelte';
  import HeadlineMarquee from './lib/HeadlineMarquee.svelte';
  import { fetchFeeds, fetchArticlesByCategory } from './lib/api';

  let selectedFeedId = null;
  let selectedCategoryId = null; // New state for selected category
  let selectedArticle = null;
  let rawArticles = [];  // main article list
  let marqueeArticles = []; // marquee article list
  let loading = false;
  let marqueeLoading = false;
  let error = null;
  let marqueeError = null;
  let feeds = [];
  let feedMap = {};
  let page = 0;
  let hasMore = true;
  const PAGE_SIZE = 100;
  
  // Add state for marquee category
  let marqueeSelectedCategoryId = null;
  let categories = [];
  let categoriesLoading = false;
  
  // category colors and icons
  const categoryColors = [
    '#f0f7ff', // light blue
    '#fff0f0', // light red
    '#f0fff0', // light green
    '#fff0ff', // light purple
    '#fffff0', // light yellow
    '#f0ffff', // light cyan
    '#f5f5f5', // light gray
    '#e6f7ff', // light blue
  ];
  
  const categoryIcons = [
    '📰', // news
    '💻', // tech
    '🔬', // science
    '🎮', // game
    '📚', // literature
    '🎬', // entertainment
    '💼', // business
    '🌍', // international
  ];
  
  // get category color by index
  function getCategoryColor(index) {
    return categoryColors[index % categoryColors.length];
  }
  
  // get category icon by index
  function getCategoryIcon(index) {
    return categoryIcons[index % categoryIcons.length];
  }
  
  // save and load user selected category
  function saveSelectedCategory(categoryId) {
    try {
      localStorage.setItem('marqueeCategoryId', categoryId || '');
    } catch (e) {
      console.error('Failed to save category to localStorage:', e);
    }
  }
  
  function loadSelectedCategory() {
    try {
      const savedCategory = localStorage.getItem('marqueeCategoryId');
      return savedCategory ? parseInt(savedCategory) : null;
    } catch (e) {
      console.error('Failed to load category from localStorage:', e);
      return null;
    }
  }

  // load articles for main article list
  async function loadAllArticles(reset = false) {
    if (reset) {
      page = 0;
      rawArticles = [];
      hasMore = true;
    }
    
    if (!hasMore || loading) return;
    
    loading = true;
    error = null;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    try {
      // always load all articles, not filtered by category
      console.log('Loading all articles for main list');
      const res = await fetch(`/rss-articles?skip=${page * PAGE_SIZE}&limit=${PAGE_SIZE}`, { signal: controller.signal });
      if (!res.ok) throw new Error(`API returned ${res.status}`);
      const text = await res.text();
      console.log('All articles response for main list');
      const newArticles = JSON.parse(text);
      
      console.log(`Loaded ${newArticles.length} articles for main list`);
      if (newArticles.length < PAGE_SIZE) {
        hasMore = false;
      }
      rawArticles = [...rawArticles, ...newArticles];
      page++;
    } catch (e) {
      if (e.name === 'AbortError') {
        error = 'Request timed out, please try again later';
      } else {
        error = e.message;
      }
      console.error('Error loading articles for main list:', e);
    } finally {
      loading = false;
      clearTimeout(timeoutId);
    }
  }

  // load articles for marquee, filtered by category
  async function loadMarqueeArticles() {
    if (marqueeLoading) return;
    
    marqueeLoading = true;
    marqueeError = null;
    try {
      // load articles for marquee, filtered by category
      if (marqueeSelectedCategoryId) {
        console.log(`Loading marquee articles for category ID: ${marqueeSelectedCategoryId}`);
        marqueeArticles = await fetchArticlesByCategory(
          marqueeSelectedCategoryId, 
          0,  // start from the beginning
          PAGE_SIZE  // use the same page size as main list, no limit
        );
      } else {
        console.log('Loading all articles for marquee');
        const res = await fetch(`/rss-articles?limit=${PAGE_SIZE}`);
        if (!res.ok) throw new Error(`API returned ${res.status}`);
        const data = await res.json();
        marqueeArticles = data;
      }
      console.log(`Loaded ${marqueeArticles.length} articles for marquee`);
    } catch (e) {
      marqueeError = e.message;
      console.error('Error loading marquee articles:', e);
    } finally {
      marqueeLoading = false;
    }
  }

  async function loadAllFeeds() {
    try {
      feeds = await fetchFeeds();
      feedMap = Object.fromEntries(feeds.map(f => [f.id, f.name]));
    } catch (e) {
      // ignore
    }
  }
  
  // Add function to load categories
  async function loadCategories() {
    try {
      categoriesLoading = true;
      const res = await fetch('/rss-feeds/categories/');
      if (!res.ok) throw new Error('Failed to fetch categories');
      categories = await res.json();
    } catch (e) {
      console.error('Failed to load categories:', e);
    } finally {
      categoriesLoading = false;
    }
  }
  
  // Add function to handle category selection for the marquee
  function handleMarqueeCategoryChange(event) {
    const categoryId = event.target.value ? parseInt(event.target.value) : null;
    console.log(`Selected marquee category ID: ${categoryId}`);
    if (marqueeSelectedCategoryId !== categoryId) {
      marqueeSelectedCategoryId = categoryId;
      // save user selected category
      saveSelectedCategory(categoryId);
      console.log(`Switching marquee to category ID: ${marqueeSelectedCategoryId}`);
      loadMarqueeArticles(); // only reload marquee articles
    }
  }



  async function handleLoadMore() {
    // Load more articles if available
    if (hasMore && !loading) {
      console.log('Loading more all articles...');
      await loadAllArticles();
    }
  }

  onMount(async () => {
    await loadCategories();
    // load user selected category
    marqueeSelectedCategoryId = loadSelectedCategory();
    // ensure category ID is valid (exists in loaded categories list)
    if (marqueeSelectedCategoryId && categories.length > 0) {
      const categoryExists = categories.some(c => c.id === marqueeSelectedCategoryId);
      if (!categoryExists) {
        marqueeSelectedCategoryId = null;
        saveSelectedCategory(null);
      }
    }
    
    // load data in parallel
    await Promise.all([
      loadAllFeeds(),
      loadAllArticles(true),
      loadMarqueeArticles()
    ]);
  });

  // main article list data processing
  $: allArticles = rawArticles
    .filter(a => a?.id && a.title && a.published_at)
    .sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

  // marquee article data processing
  $: processedMarqueeArticles = marqueeArticles
    .filter(a => a?.id && a.title && a.published_at)
    .sort((a, b) => new Date(b.published_at).getTime() - new Date(a.published_at).getTime());

  $: {
    console.log(`Computed articles - Main list: ${allArticles.length}, Marquee: ${processedMarqueeArticles.length}, selected category: ${marqueeSelectedCategoryId}`);
  }

  function handleFeedSelect(event) {
    const { feedId, categoryId } = event.detail;
    selectedFeedId = feedId;
    selectedCategoryId = categoryId;
    selectedArticle = null;
    console.log(`Selected feed: ${selectedFeedId}, category: ${selectedCategoryId}`);
  }

  function handleArticleSelect(event) {
    const article = event.detail.article;
    if (selectedArticle && selectedArticle.id === article.id) {
      selectedArticle = null;
    } else {
      selectedArticle = article;
    }
  }
</script>

<main>
  <header class="header">
    <h1>Forarger Stream</h1>
  </header>

  <!-- Marquee section hidden -->
  <!--
  <section class="marquee-container">
    <div class="marquee-controls">
      <select on:change={handleMarqueeCategoryChange} class="category-select">
        <option value="">🌐 All categories</option>
        {#each categories as category, i}
          <option value={category.id} style="background-color: {getCategoryColor(i)};" 
                  selected={marqueeSelectedCategoryId === category.id}>
            {getCategoryIcon(i)} {category.name}
          </option>
        {/each}
      </select>
    </div>
    {#if marqueeLoading}
      <div class="skeleton-marquee"></div>
    {:else}
      {#if marqueeError}
        <div class="marquee-error">Marquee load error: {marqueeError}</div>
      {/if}
      <HeadlineMarquee articles={processedMarqueeArticles} />
    {/if}
  </section>
  -->

  <div class="layout">
    <aside class="sidebar">
      <FeedList on:select={handleFeedSelect} />
    </aside>
    <section class="main-content {selectedArticle ? 'with-detail' : ''}">
      <div class="article-list">
        <ArticleList
          feedId={selectedFeedId}
          categoryId={selectedCategoryId}
          allArticles={allArticles}
          paused={!!selectedArticle}
          selectedArticle={selectedArticle}
          feedMap={feedMap}
          on:select={handleArticleSelect}
          on:loadMore={handleLoadMore}
        />
        {#if loading && page > 0}
          <div class="loading-more">Loading more articles...</div>
        {/if}
      </div>
      {#if selectedArticle}
        <div class="article-detail">
          <ArticleDetail article={selectedArticle} on:close={() => selectedArticle = null} />
        </div>
      {/if}
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

  :global(html) {
    font-size: 70%;
  }

  :global(body) {
    margin: 0;
    font-size: 1.4rem;
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
  .header h1,
  .feed-header h2,
  .article-title {
    margin: 0;
    color: var(--color-primary);
    font-size: 1rem; /* 11px */
  }

  .marquee-container {
    position: sticky; top: 64px;
    background: var(--color-surface);
    padding: var(--spacing);
    border-bottom: 1px solid var(--color-border);
    z-index: 9;
  }
  
  .marquee-controls {
    display: flex;
    justify-content: flex-end;
    margin-bottom: 0.5rem;
  }
  
  .category-select {
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 0.25rem 0.5rem;
    font-size: 0.9rem;
    background-color: white;
    color: var(--color-text);
    cursor: pointer;
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='none' stroke='%23666' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l-6-6h12z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 0.5rem center;
    padding-right: 1.5rem;
    transition: all 0.2s ease;
  }
  
  .category-select:hover {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.1);
  }
  
  .category-select:focus {
    outline: none;
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px rgba(74, 144, 226, 0.2);
  }
  
  .category-select option {
    padding: 8px;
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
    /* overflow-y: auto; */
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

  /* dynamic two/three column switch */
  .main-content:not(.with-detail) .article-list {
    width: 100%;
  }
  .main-content:not(.with-detail) .article-detail {
    display: none;
  }

  .loading-more {
    text-align: center;
    padding: 1rem;
    color: var(--color-text-secondary);
    font-size: 0.9rem;
  }
</style>
