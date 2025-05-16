<script>
  /** @type {{id: string, title: string, published_at: string}[]} */
  export let articles = [];

  // each title scroll duration (seconds)
  const perTitleDuration = 20;

  // divide articles into two rows
  $: row1 = articles.filter((_, i) => i % 2 === 0);
  $: row2 = articles.filter((_, i) => i % 2 === 1);

  $: duration1 = `${row1.length * perTitleDuration}s`;
  $: duration2 = `${row2.length * perTitleDuration}s`;

  // pause animation when mouse hover
  let paused = false;
</script>

<div class="marquee-multiline" on:mouseenter={() => (paused = true)} on:mouseleave={() => (paused = false)}>
  <div
    class="marquee"
  >
    <div
      class="marquee-content"
      style="--duration: {duration1}; animation-play-state: {paused ? 'paused' : 'running'}"
    >
      {#each row1 as article (article.id)}
        <span class="headline">{article.title}</span>
      {/each}
      {#each row1 as article (article.id + '-copy')}
        <span class="headline">{article.title}</span>
      {/each}
    </div>
  </div>
  <div
    class="marquee"
  >
    <div
      class="marquee-content"
      style="--duration: {duration2}; animation-play-state: {paused ? 'paused' : 'running'}"
    >
      {#each row2 as article (article.id)}
        <span class="headline">{article.title}</span>
      {/each}
      {#each row2 as article (article.id + '-copy')}
        <span class="headline">{article.title}</span>
      {/each}
    </div>
  </div>
</div>

<style>
.marquee-multiline {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  background: #f0f7ff;
  padding: 0.2rem 0;
}
.marquee {
  overflow: hidden;
  height: 2.2rem;
  display: flex;
  align-items: center;
}
.marquee-content {
  display: inline-block;
  white-space: nowrap;
  /* read duration from variable */
  animation: scroll-left var(--duration) linear infinite;
}
.headline {
  display: inline-block;
  margin: 0 2rem;
  font-weight: bold;
  cursor: pointer;
}
@keyframes scroll-left {
  0%   { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
</style>
