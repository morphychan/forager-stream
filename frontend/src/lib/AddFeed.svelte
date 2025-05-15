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
      error = '请输入RSS订阅源URL';
      return;
    }
    
    try {
      loading = true;
      error = null;
      
      await createFeed({ url: url.trim() });
      
      // 重置表单
      url = '';
      showForm = false;
      
      // 通知父组件刷新订阅源列表
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
      // 重置表单状态
      url = '';
      error = null;
    }
  }
</script>

<div class="add-feed">
  <button class="add-btn" on:click={toggleForm}>
    {showForm ? '取消' : '添加订阅源'}
  </button>
  
  {#if showForm}
    <div class="add-form">
      <form on:submit|preventDefault={handleSubmit}>
        <input 
          type="url" 
          placeholder="输入RSS订阅源URL" 
          bind:value={url}
          disabled={loading}
        />
        <button type="submit" disabled={loading}>
          {loading ? '添加中...' : '添加'}
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