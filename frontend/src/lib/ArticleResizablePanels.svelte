<script>
  import { onMount } from 'svelte';
  
  export let leftMinWidth = 300;
  export let rightMinWidth = 400;
  export let initialLeftWidth = 400;
  export let showDetail = false;
  
  let container;
  let leftPanel;
  let rightPanel;
  let resizer;
  let isResizing = false;
  let leftWidth = initialLeftWidth;
  
  onMount(() => {
    // Load saved width from localStorage
    const savedWidth = localStorage.getItem('articleListWidth');
    
    if (savedWidth) {
      leftWidth = parseInt(savedWidth);
    }
    
    // Apply initial width
    if (leftPanel) {
      leftPanel.style.width = `${leftWidth}px`;
    }
  });
  
  function startResize(event) {
    // Only allow resizing when detail is shown
    if (!showDetail) return;
    
    isResizing = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    event.preventDefault();
  }
  
  function handleResize(event) {
    if (!isResizing || !container || !showDetail) return;
    
    const containerRect = container.getBoundingClientRect();
    const newLeftWidth = event.clientX - containerRect.left;
    const containerWidth = containerRect.width;
    const maxLeftWidth = containerWidth - rightMinWidth - 2; // 2px for resizer width
    
    // Constrain the width
    if (newLeftWidth >= leftMinWidth && newLeftWidth <= maxLeftWidth) {
      leftWidth = newLeftWidth;
      leftPanel.style.width = `${leftWidth}px`;
      
      // Save to localStorage
      localStorage.setItem('articleListWidth', leftWidth.toString());
    }
  }
  
  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
</script>

<div class="resizable-container" bind:this={container}>
  <div 
    class="left-panel" 
    bind:this={leftPanel} 
    style="width: {showDetail ? leftWidth + 'px' : '100%'};"
    class:full-width={!showDetail}
  >
    <slot name="left" />
  </div>
  
  {#if showDetail}
    <div 
      class="resizer" 
      bind:this={resizer}
      on:mousedown={startResize}
      class:resizing={isResizing}
    >
      <div class="resizer-line"></div>
    </div>
    
    <div class="right-panel" bind:this={rightPanel}>
      <slot name="right" />
    </div>
  {/if}
</div>

<style>
  .resizable-container {
    display: flex;
    height: 100%;
    width: 100%;
    overflow: hidden;
  }
  
  .left-panel {
    flex-shrink: 0;
    overflow: hidden;
    background: var(--color-surface, #ffffff);
    transition: width 0.3s ease;
    margin: 8px 1px 8px 8px;
  }
  
  .left-panel.full-width {
    width: 100% !important;
    margin: 8px;
  }
  
  .right-panel {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    background: var(--color-surface, #ffffff);
    margin: 8px 8px 8px 1px;
    /* Force scrollbar to be visible for debugging */
    height: 100%;
    max-height: 100vh;
    /* Ensure scrollbar is visible */
    scrollbar-width: thin;
    scrollbar-color: #c1c1c1 transparent;
  }
  
  /* Webkit scrollbar styling */
  .right-panel::-webkit-scrollbar {
    width: 8px;
  }
  
  .right-panel::-webkit-scrollbar-track {
    background: transparent;
  }
  
  .right-panel::-webkit-scrollbar-thumb {
    background-color: #c1c1c1;
    border-radius: 4px;
  }
  
  .right-panel::-webkit-scrollbar-thumb:hover {
    background-color: #a1a1a1;
  }
  
  .resizer {
    width: 2px;
    background: transparent;
    cursor: col-resize;
    position: relative;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
    margin: 8px 0;
  }
  
  .resizer:hover {
    background: rgba(74, 144, 226, 0.1);
  }
  
  .resizer.resizing {
    background: rgba(74, 144, 226, 0.2);
  }
  
  .resizer-line {
    width: 1px;
    height: 100%;
    background: var(--color-border, #e0e0e0);
    transition: background-color 0.2s ease;
    border-radius: 0.5px;
  }
  
  .resizer:hover .resizer-line,
  .resizer.resizing .resizer-line {
    background: var(--color-primary, #4a90e2);
    width: 2px;
  }
  
  /* Add visual feedback when resizing */
  .resizer::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 8px;
    height: 20px;
    background: transparent;
    border-radius: 2px;
    opacity: 0;
    transition: opacity 0.2s ease;
    z-index: 5;
  }
  
  .resizer:hover::before,
  .resizer.resizing::before {
    opacity: 1;
    background: var(--color-primary, #4a90e2);
  }
  
  /* Mobile responsiveness */
  @media (max-width: 768px) {
    .resizable-container {
      flex-direction: column;
    }
    
    .resizer {
      display: none;
    }
    
    .left-panel {
      width: 100% !important;
    }
    
    .right-panel {
      flex: 1;
    }
  }
</style> 