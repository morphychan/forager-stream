<script>
  import { createEventDispatcher } from 'svelte';
  import { createFeed } from './api';
  
  const dispatch = createEventDispatcher();
  
  let url = '';
  let loading = false;
  let error = null;
  let showForm = false;
  
  async function handleSubmit() {
    if (!url.trim()) {
      error = 'Please enter an RSS feed URL';
      return;
    }
    
    try {
      loading = true;
      error = null;
      
      await createFeed({ url: url.trim() });
      
      // Reset form
      url = '';
      showForm = false;
      
      // Notify parent component to refresh the feed list
      dispatch('feedAdded');
      
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  function toggleForm() {
    showForm = !showForm;
    if (!showForm) {
      // Reset form state
      url = '';
      error = null;
    }
  }
</script>

<div class="add-feed">
  <button class="add-btn" on:click={toggleForm}>
    {showForm ? 'Cancel' : 'Add Feed'}
  </button>
  
  {#if showForm}
    <div class="add-form">
      <form on:submit|preventDefault={handleSubmit}>
        <input 
          type="url" 
          placeholder="Enter RSS feed URL" 
          bind:value={url}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Adding...' : 'Add'}
        </button>
      </form>
      
      {#if error}
        <div class="error-message">{error}</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .add-feed {
    margin-bottom: 15px;
  }
  
  .add-btn {
    width: 100%;
    margin-bottom: 10px;
  }
  
  .add-form {
    background-color: #f9f9f9;
    padding: 10px;
    border-radius: 4px;
    border: 1px solid #ddd;
  }
  
  form {
    display: flex;
    gap: 8px;
  }
  
  input {
    flex: 1;
    padding: 8px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 14px;
  }
  
  .error-message {
    color: #dc3545;
    font-size: 14px;
    margin-top: 8px;
  }
  
  body {
    font-size: 14px;
  }
</style> 