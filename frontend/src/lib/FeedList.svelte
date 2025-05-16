<script lang="ts">
  /// <reference lib="dom" />
  /// <reference lib="es2015" />
  
  // @ts-nocheck
  import { createEventDispatcher, onMount } from 'svelte';
  import { fetchFeeds, deleteFeed } from './api';
  import AddFeed from './AddFeed.svelte';
  
  const dispatch = createEventDispatcher();
  let feeds = [];
  let loading = true;
  let error = null;
  let selectedFeedId = null;
  
  onMount(async () => {
    await loadFeeds();
  });
  
  /** Load the list of feeds from the backend */
  async function loadFeeds() {
    try {
      loading = true;
      feeds = await fetchFeeds();
      console.log('feeds:', feeds);
      if (feeds.length > 0 && !selectedFeedId) {
        selectFeed(feeds[0].id);
      }
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  /** Mark a feed as selected and notify parent */
  function selectFeed(feedId) {
    selectedFeedId = feedId;
    dispatch('select', { feedId });
  }
  
  /** Delete a feed and update the list */
  async function handleDeleteFeed(feedId, event) {
    event.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this feed?')) {
      return;
    }
    
    try {
      await deleteFeed(feedId);
      feeds = feeds.filter(f => f.id !== feedId);
      
      if (selectedFeedId === feedId) {
        if (feeds.length > 0) {
          selectFeed(feeds[0].id);
        } else {
          selectedFeedId = null;
          dispatch('select', { feedId: null });
        }
      }
    } catch (err) {
      alert(`Failed to delete: ${err.message}`);
    }
  }
  
  /** Refresh list when a new feed is added */
  function handleFeedAdded() {
    loadFeeds();
  }
</script>

<div class="feed-list">
  <header class="feed-header">
    <h2>RSS Feeds</h2>
  </header>
  
  <AddFeed on:feedAdded={handleFeedAdded} />
  
  {#if loading}
    <div class="status-message">Loading...</div>
  {:else if error}
    <div class="status-message error">
      <p>{error}</p>
      <button class="btn" on:click={loadFeeds}>Retry</button>
    </div>
  {:else if feeds.length === 0}
    <div class="status-message empty">
      <p>No feeds yet. Please add one.</p>
    </div>
  {:else}
    <ul class="feed-items">
      {#each feeds as feed (feed.id)}
        <li 
          class="feed-item {selectedFeedId === feed.id ? 'selected' : ''}" 
          on:click={() => selectFeed(feed.id)}
        >
          <span class="feed-title" data-url={feed.url}>
            {feed.name}
          </span>
          <button 
            class="delete-btn" 
            on:click={(e) => handleDeleteFeed(feed.id, e)}
          >
            ×
          </button>
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
    border-right: 1px solid var(--color-border);
    padding: 1.2rem 0.75rem 1.2rem 0.75rem;
    background: var(--color-surface);
    font-family: var(--font-family);
    min-width: 270px;
  }

  .feed-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.2rem;
  }

  .feed-header h2 {
    font-size: var(--font-size-lg);
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
    gap: 0.7rem;
  }

  .feed-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.85rem 1rem;
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
    font-size: var(--font-size-lg);
    letter-spacing: 0.2px;
  }

  /* Feed URL（如果没有title时显示） */
  .feed-title:empty::before {
    content: attr(data-url);
    color: var(--color-text-secondary);
    font-style: italic;
    font-size: 0.98rem;
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

  /* AddFeed按钮样式微调 */
  :global(.add-feed-btn) {
    margin-bottom: 1.2rem;
    width: 100%;
    border-radius: var(--radius);
    box-shadow: var(--shadow-elevation-1);
  }

  @media (max-width: 700px) {
    .feed-list {
      min-width: 100vw;
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
</style>
