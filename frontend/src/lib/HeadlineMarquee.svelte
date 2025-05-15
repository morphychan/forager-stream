<script>
  /** @type {{id: string, title: string, published_at: string}[]} */
  export let articles = [];
  // 按发布时间从新到旧排序
  $: sortedArticles = Array.isArray(articles) ? [...articles].sort((a, b) => new Date(b.published_at) - new Date(a.published_at)) : [];

  // 鼠标悬浮暂停
  let marqueePaused = false;
  let marqueeContent;

  // 点击标题时触发事件（可选）
  function handleClick(article) {
    // 可自定义跳转或事件
    // dispatch('select', { article });
  }
</script>

<div class="marquee" on:mouseenter={() => marqueePaused = true} on:mouseleave={() => marqueePaused = false}>
  <div class="marquee-content" bind:this={marqueeContent} style="animation-play-state: {marqueePaused ? 'paused' : 'running'};">
    {#each sortedArticles as article (article.id)}
      <span class="headline" on:click={() => handleClick(article)}>{article.title}</span>
    {/each}
    <!-- 复制一份内容以实现无缝循环 -->
    {#each sortedArticles as article (article.id + '-copy')}
      <span class="headline" on:click={() => handleClick(article)}>{article.title}</span>
    {/each}
  </div>
</div>

<style>
.marquee {
  width: 100%;
  overflow: hidden;
  background: #f0f7ff;
  border-bottom: 1.5px solid #e0e6ed;
  height: 2.2rem;
  display: flex;
  align-items: center;
  user-select: none;
}
.marquee-content {
  display: inline-block;
  white-space: nowrap;
  animation: scroll-left 20s linear infinite;
  font-size: 1rem;
  min-width: 100%;
}
.headline {
  display: inline-block;
  margin: 0 2rem;
  font-weight: bold;
  color: #357ae8;
  cursor: pointer;
  transition: color 0.2s;
}
.headline:hover {
  color: #174ea6;
  text-decoration: underline;
}
@keyframes scroll-left {
  0% { transform: translateX(0%);}
  100% { transform: translateX(-50%);}
}
</style> 