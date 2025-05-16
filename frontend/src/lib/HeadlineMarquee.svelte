<script>
  /** @type {{id: string, title: string, published_at: string}[]} */
  export let articles = [];

  // each title scroll duration (seconds)
  const perTitleDuration = 15;
  // calculate total duration, like "15s"
  $: duration = `${articles.length * perTitleDuration}s`;

  // pause animation when mouse hover
  let paused = false;
</script>

<div
  class="marquee"
  on:mouseenter={() => (paused = true)}
  on:mouseleave={() => (paused = false)}
>
  <div
    class="marquee-content"
    style="--duration: {duration}; animation-play-state: {paused ? 'paused' : 'running'}"
  >
    {#each articles as article (article.id)}
      <span class="headline">{article.title}</span>
    {/each}
    {#each articles as article (article.id + '-copy')}
      <span class="headline">{article.title}</span>
    {/each}
  </div>
</div>

<style>
.marquee {
  overflow: hidden;
  background: #f0f7ff;
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
