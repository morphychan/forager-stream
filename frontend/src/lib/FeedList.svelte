<script lang="ts">
  /// <reference lib="dom" />
  /// <reference lib="es2015" />
  
  // @ts-nocheck
  import { createEventDispatcher, onMount } from 'svelte';
  import { deleteFeed } from './api';

const dispatch = createEventDispatcher();
  let categories = [];
  let categoriesLoading = true;
  let error = null;
  let selectedFeedId = null;
  let selectedCategoryId = null; // Track the selected category
  let expandedCategoryId = null; // current expanded category id
  let feedsMap = {}; // { categoryId: Feed[] }
  let feedsLoadingMap = {}; // { categoryId: boolean }
  let allFeeds = [];
  let allFeedsLoading = false;
  
  onMount(async () => {
    await loadCategories();
  });
  
    // This function has been replaced by fetchFeedsByCategory
  
  /** Mark a feed as selected and notify parent */
  function selectFeed(feedId, event) {
    event.stopPropagation(); // Stop the click from bubbling up to parent category
    selectedFeedId = feedId;
    dispatch('select', { 
      feedId,
      categoryId: expandedCategoryId // Send the current category ID
    });
  }
  
  /** Delete a feed and update the list */
  async function handleDeleteFeed(feedId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this feed?')) {
      return;
    }
    
    try {
      await deleteFeed(feedId);
      
      // If we're viewing a category, update its feeds
      if (expandedCategoryId !== null && feedsMap[expandedCategoryId]) {
        feedsMap[expandedCategoryId] = feedsMap[expandedCategoryId].filter(f => f.id !== feedId);
      }
      
      // If this was the selected feed, select either the first feed in the category or none
      if (selectedFeedId === feedId) {
        if (expandedCategoryId !== null && feedsMap[expandedCategoryId]?.length > 0) {
          selectFeed(feedsMap[expandedCategoryId][0].id, event);
        } else {
          // No feeds left in this category or viewing all feeds - select none (virtual "All Feeds")
          selectFeed(null, event);
        }
      }
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    }
  }

  // Get all categories
  async function loadCategories() {
    try {
      categoriesLoading = true;
      const res = await fetch('/rss-feeds/categories/');
      if (!res.ok) throw new Error('Failed to fetch categories');
      categories = await res.json();
    } catch (err) {
      error = err.message;
    } finally {
      categoriesLoading = false;
    }
  }

  async function toggleCategory(categoryId, event) {
    if (expandedCategoryId === categoryId) {
      // Collapse the category
      expandedCategoryId = null;
      // When collapsing, we select the category to show all its articles
      selectedCategoryId = categoryId;
      selectedFeedId = null;
      dispatch('select', { feedId: null, categoryId });
    } else {
      // Expand the category
      expandedCategoryId = categoryId;
      if (!feedsMap[categoryId]) {
        feedsLoadingMap[categoryId] = true;
        feedsMap[categoryId] = await fetchFeedsByCategory(categoryId);
        feedsLoadingMap[categoryId] = false;
      }
      
      // When expanding a category, also show all its articles
      selectedCategoryId = categoryId;
      selectedFeedId = null;
      dispatch('select', { feedId: null, categoryId });
    }
  }

  async function showAllFeeds(event) {
    expandedCategoryId = null;
    selectedCategoryId = null;
    selectedFeedId = null;

    // Notify parent that all feeds are selected (null feedId and categoryId)
    dispatch('select', { feedId: null, categoryId: null });
  }

  async function fetchFeedsByCategory(categoryId = null) {
    let url = '/rss-feeds/';
    if (categoryId) {
      url += `?category_id=${categoryId}`;
    }
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch RSS feeds');
    return await response.json();
  }
</script>

<div class="feed-list">
  <header class="feed-header">
    <h2>RSS Feeds</h2>
  </header>
  
  {#if categoriesLoading}
    <div class="status-message">Loading...</div>
  {:else if error}
    <div class="status-message error">
      <p>{error}</p>
      <button class="btn" on:click={(e) => { loadCategories(); if (expandedCategoryId === null) showAllFeeds(e); else if (expandedCategoryId) toggleCategory(expandedCategoryId, e); }}>Retry</button>
    </div>
  {:else}
    <ul class="category-list">
      <li class="category-item {expandedCategoryId === null && !selectedCategoryId ? 'selected' : ''}" on:click={(e) => showAllFeeds(e)}>
        <span>All Feeds</span>
      </li>
      {#each categories as category}
        <li class="category-item {expandedCategoryId === category.id || (!selectedFeedId && selectedCategoryId === category.id) ? 'selected' : ''}" on:click={(e) => toggleCategory(category.id, e)}>
          <span>{category.name.charAt(0).toUpperCase() + category.name.slice(1)}</span>
          {#if expandedCategoryId === category.id}
            {#if feedsLoadingMap[category.id]}
              <div class="status-message">Loading...</div>
            {:else}
              <ul class="feed-items">
                {#each feedsMap[category.id] || [] as feed (feed.id)}
                  <li class="feed-item {selectedFeedId === feed.id ? 'selected' : ''}" on:click={(e) => selectFeed(feed.id, e)}>
                    <span class="feed-title" data-url={feed.url}>{feed.name}</span>
                    <button class="delete-btn" on:click={(e) => handleDeleteFeed(feed.id, e)}>×</button>
                  </li>
                {/each}
              </ul>
            {/if}
          {/if}
        </li>
      {/each}
    </ul>
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

  .feed-list {
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 1rem 0.6rem;
    background: var(--color-surface);
    font-family: var(--font-family);
    min-width: 160px;
    max-width: 240px;
  }

  .feed-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .feed-header h2 {
    font-size: 1.1rem;
    color: var(--color-text-primary);
    font-weight: 700;
    letter-spacing: 1px;
  }

  .btn {
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
  }
  .btn:hover,
  .btn:focus {
    background: var(--color-brand-hover);
    box-shadow: var(--shadow-elevation-2);
    transform: translateY(-2px) scale(1.04);
  }

  .status-message {
    text-align: center;
    padding: 1.2rem 0.5rem;
    color: var(--color-text-secondary);
    font-size: var(--font-size-lg);
    border-radius: var(--radius);
    background: #fff;
    box-shadow: var(--shadow-elevation-1);
    margin: 1.5rem 0.5rem;
  }
  .status-message.error {
    color: #dc3545;
    background: #fff0f2;
  }
  .status-message.empty {
    color: var(--color-text-secondary);
    background: #f8fafc;
  }

  .feed-items {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .feed-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.08rem 0.8rem;
    min-height: 1.5rem;
    background: #fff;
    border-radius: var(--radius);
    box-shadow: var(--shadow-elevation-1);
    border: 1.5px solid transparent;
    cursor: pointer;
    transition: box-shadow 0.18s, border 0.18s, background 0.18s, transform 0.12s;
    margin-bottom: 0;
    position: relative;
  }
  .feed-item:hover {
    box-shadow: var(--shadow-elevation-2);
    background: #f0f7ff;
    transform: translateY(-2px) scale(1.02);
  }
  .feed-item.selected {
    background: linear-gradient(90deg, #e3f0ff 60%, #f7fafd 100%);
    border-left: 4px solid #4f8cff;
    border-color: #4f8cff;
    box-shadow: 0 4px 16px rgba(80, 120, 200, 0.16);
  }

  .feed-title {
    flex: 1;
    font-weight: 600;
    color: var(--color-text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 0.85rem;
    line-height: 1.1;
    letter-spacing: 0.2px;
  }

  /* Display feed URL if no title is available */
  .feed-title:empty::before {
    content: attr(data-url);
    color: var(--color-text-secondary);
    font-style: italic;
    font-size: 0.85rem;
  }

  .delete-btn {
    background: transparent;
    border: none;
    font-size: 1.15rem;
    line-height: 1;
    padding: 0.25rem 0.4rem;
    margin-left: 0.5rem;
    color: var(--color-text-secondary);
    visibility: hidden;
    border-radius: 50%;
    transition: color 0.2s, background 0.2s;
  }
  .feed-item:hover .delete-btn {
    visibility: visible;
    background: #fbeaec;
  }
  .delete-btn:hover,
  .delete-btn:focus {
    color: #c82333;
    background: #ffe6ea;
    outline: none;
  }

  /* Remove AddFeed button styles */
  @media (max-width: 700px) {
    .feed-list {
      width: 100%;
      border-right: none;
      border-bottom: 1px solid var(--color-border);
      padding: 0.7rem 0.3rem;
    }
    .feed-header {
      flex-direction: column;
      gap: 0.5rem;
    }
  }

  body {
    font-size: 14px;
  }

  .category-list {
    list-style: none;
    margin: 0 0 1rem 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .category-item {
    padding: 0.2rem 0.8rem;
    border-radius: var(--radius);
    cursor: pointer;
    background: #f5f7fa;
    color: #4f8cff;
    font-weight: 600;
    transition: background 0.18s, color 0.18s;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 1rem;
  }
  .category-item.selected {
    background: linear-gradient(90deg, #e3f0ff 60%, #f7fafd 100%);
    color: #357ae8;
  }
</style>
