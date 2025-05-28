<script lang="ts">
  import { onMount } from 'svelte';
  
  export let leftMinWidth = 200;
  export let rightMinWidth = 300;
  export let initialLeftWidth = 260;
  
  let container;
  let leftPanel;
  let rightPanel;
  let resizer;
  let isResizing = false;
  let leftWidth = initialLeftWidth;
  let isCollapsed = false;
  let savedLeftWidth = initialLeftWidth; // Store the width before collapse
  
  onMount(() => {
    // Load saved width from localStorage
    const savedWidth = localStorage.getItem('feedListWidth');
    const savedCollapsedState = localStorage.getItem('feedListCollapsed');
    
    if (savedWidth) {
      savedLeftWidth = parseInt(savedWidth);
      leftWidth = savedLeftWidth;
    }
    
    if (savedCollapsedState === 'true') {
      isCollapsed = true;
      leftWidth = 0;
    }
    
    // Apply initial width
    if (leftPanel) {
      leftPanel.style.width = `${leftWidth}px`;
    }
  });
  
  function startResize(event) {
    // Don't allow resizing when collapsed
    if (isCollapsed) return;
    
    isResizing = true;
    document.addEventListener('mousemove', handleResize);
    document.addEventListener('mouseup', stopResize);
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    event.preventDefault();
  }
  
  function handleResize(event) {
    if (!isResizing || !container || isCollapsed) return;
    
    const containerRect = container.getBoundingClientRect();
    const newLeftWidth = event.clientX - containerRect.left;
    const containerWidth = containerRect.width;
    const maxLeftWidth = containerWidth - rightMinWidth - 4; // 4px for resizer width
    
    // Constrain the width
    if (newLeftWidth >= leftMinWidth && newLeftWidth <= maxLeftWidth) {
      leftWidth = newLeftWidth;
      savedLeftWidth = newLeftWidth; // Save the current width
      leftPanel.style.width = `${leftWidth}px`;
      
      // Save to localStorage
      localStorage.setItem('feedListWidth', savedLeftWidth.toString());
    }
  }
  
  function stopResize() {
    isResizing = false;
    document.removeEventListener('mousemove', handleResize);
    document.removeEventListener('mouseup', stopResize);
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
  }
  
  function toggleCollapse() {
    isCollapsed = !isCollapsed;
    
    if (isCollapsed) {
      // Store current width before collapsing
      if (leftWidth > 0) {
        savedLeftWidth = leftWidth;
        localStorage.setItem('feedListWidth', savedLeftWidth.toString());
      }
      leftWidth = 0;
    } else {
      // Restore previous width
      leftWidth = savedLeftWidth || initialLeftWidth;
    }
    
    // Apply the new width with animation
    if (leftPanel) {
      leftPanel.style.width = `${leftWidth}px`;
    }
    
    // Save collapsed state
    localStorage.setItem('feedListCollapsed', isCollapsed.toString());
  }
</script>

<div class="resizable-container" bind:this={container}>
  <div class="left-panel" bind:this={leftPanel} style="width: {leftWidth}px;" class:collapsed={isCollapsed}>
    <slot name="left" />
  </div>
  
  <div 
    class="resizer" 
    bind:this={resizer}
    on:mousedown={startResize}
    class:resizing={isResizing}
    class:collapsed={isCollapsed}
  >
    <div class="resizer-line"></div>
    <button 
      class="collapse-toggle" 
      on:click={toggleCollapse}
      title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      <svg 
        class="arrow-icon" 
        class:collapsed={isCollapsed}
        width="24" 
        height="24" 
        viewBox="0 0 24 24" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <!-- Triangle pointing left when expanded (can collapse) -->
        <!-- Triangle pointing right when collapsed (can expand) -->
        <path 
          d="M15 6L8 12L15 18Z" 
          fill="currentColor"
        />
      </svg>
    </button>
  </div>
  
  <div class="right-panel" bind:this={rightPanel}>
    <slot name="right" />
  </div>
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
  }
  
  .left-panel.collapsed {
    width: 0 !important;
  }
  
  .right-panel {
    flex: 1;
    overflow: hidden;
    background: var(--color-surface, #ffffff);
  }
  
  .resizer {
    width: 4px;
    background: transparent;
    cursor: col-resize;
    position: relative;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background-color 0.2s ease;
  }
  
  .resizer.collapsed {
    cursor: default;
  }
  
  .resizer:not(.collapsed):hover {
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
  }
  
  .resizer:not(.collapsed):hover .resizer-line,
  .resizer.resizing .resizer-line {
    background: var(--color-primary, #4a90e2);
    width: 2px;
  }
  
  /* Collapse/Expand toggle button */
  .collapse-toggle {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    width: 22px;
    height: 22px;
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid rgba(74, 144, 226, 0.15);
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #666666;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10;
    padding: 0;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.06);
    backdrop-filter: blur(10px);
  }
  
  .collapse-toggle:hover {
    background: linear-gradient(135deg, #4a90e2 0%, #357ae8 100%);
    color: white;
    border-color: transparent;
    transform: translateX(-50%) scale(1.1);
    box-shadow: 0 6px 20px rgba(74, 144, 226, 0.25), 0 2px 8px rgba(74, 144, 226, 0.15);
  }
  
  .collapse-toggle:active {
    transform: translateX(-50%) scale(0.95);
    transition-duration: 0.1s;
  }
  
  /* Add a subtle pulse animation */
  .collapse-toggle::before {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    border-radius: 50%;
    border: 2px solid rgba(74, 144, 226, 0.3);
    opacity: 0;
    transform: scale(0.8);
    animation: pulse-ring 3s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
  
  @keyframes pulse-ring {
    0% {
      transform: scale(0.8);
      opacity: 0;
    }
    40% {
      transform: scale(1);
      opacity: 0.3;
    }
    80%, 100% {
      transform: scale(1.2);
      opacity: 0;
    }
  }
  
  .arrow-icon {
    transition: transform 0.3s ease;
  }
  
  .arrow-icon.collapsed {
    transform: rotate(180deg);
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
  
  .resizer:not(.collapsed):hover::before,
  .resizer.resizing::before {
    opacity: 1;
    background: var(--color-primary, #4a90e2);
  }
  
  /* Hide the visual feedback when collapsed to avoid conflicts with button */
  .resizer.collapsed::before {
    display: none;
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
      max-height: 200px;
    }
    
    .left-panel.collapsed {
      width: 100% !important;
      max-height: 0 !important;
      overflow: hidden;
    }
  }
</style> 