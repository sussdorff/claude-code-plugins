/**
 * LinkedIn Feed Extractor
 *
 * Extracts posts from the LinkedIn feed.
 * Filters out ads/promoted content and UI noise.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on LinkedIn feed (/feed/)
 * - Should scroll to load more posts before extraction
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on the feed
    if (!url.includes('/feed')) {
      return {
        success: false,
        error: 'Not on LinkedIn feed. Expected URL containing /feed'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    // Noise patterns to filter
    const isPromoted = (el) => {
      const text = el.textContent || '';
      return text.includes('Promoted') ||
             text.includes('Suggested') ||
             el.querySelector('[data-ad-banner]') !== null;
    };

    // Find all feed posts
    const feedContainer = document.querySelector('.scaffold-finite-scroll__content');
    if (!feedContainer) {
      return {
        success: false,
        error: 'Could not find feed container'
      };
    }

    const postElements = feedContainer.querySelectorAll('.feed-shared-update-v2');
    const posts = [];

    postElements.forEach((postEl, index) => {
      // Skip promoted posts
      if (isPromoted(postEl)) return;

      // Extract author info
      const authorEl = postEl.querySelector('.update-components-actor__name span[aria-hidden="true"]');
      const author = authorEl ? clean(authorEl.textContent) : '';

      const authorHeadlineEl = postEl.querySelector('.update-components-actor__description span[aria-hidden="true"]');
      const authorHeadline = authorHeadlineEl ? clean(authorHeadlineEl.textContent) : '';

      // Extract timestamp
      const timeEl = postEl.querySelector('.update-components-actor__sub-description span[aria-hidden="true"]');
      const timestamp = timeEl ? clean(timeEl.textContent) : '';

      // Extract post content
      const contentEl = postEl.querySelector('.feed-shared-update-v2__description, .update-components-text');
      let content = '';
      if (contentEl) {
        // Get visible text, handle "see more" truncation
        const seeMoreBtn = contentEl.querySelector('.see-more');
        content = clean(contentEl.textContent);
        if (seeMoreBtn) {
          content += ' [truncated - click "see more" for full text]';
        }
      }

      // Extract engagement metrics
      const reactionsEl = postEl.querySelector('.social-details-social-counts__reactions-count');
      const reactions = reactionsEl ? clean(reactionsEl.textContent) : '0';

      const commentsEl = postEl.querySelector('.social-details-social-counts__comments');
      const comments = commentsEl ? clean(commentsEl.textContent) : '0';

      const repostsEl = postEl.querySelector('.social-details-social-counts__item--with-social-proof');
      const reposts = repostsEl ? clean(repostsEl.textContent) : '';

      // Extract any shared article/link
      let sharedArticle = null;
      const articleEl = postEl.querySelector('.update-components-article');
      if (articleEl) {
        const articleTitle = articleEl.querySelector('.update-components-article__title');
        const articleSource = articleEl.querySelector('.update-components-article__meta');
        sharedArticle = {
          title: articleTitle ? clean(articleTitle.textContent) : '',
          source: articleSource ? clean(articleSource.textContent) : ''
        };
      }

      // Only include posts with actual content
      if (author || content) {
        posts.push({
          index: index + 1,
          author: author,
          authorHeadline: authorHeadline,
          timestamp: timestamp,
          content: content.slice(0, 1000), // Truncate very long posts
          reactions: reactions,
          comments: comments,
          reposts: reposts,
          sharedArticle: sharedArticle
        });
      }
    });

    return {
      success: true,
      postCount: posts.length,
      posts: posts.slice(0, 20), // Limit to 20 posts to avoid huge responses
      metadata: {
        url: url,
        extractedAt: new Date().toISOString(),
        totalPostsFound: postElements.length,
        promotedFiltered: postElements.length - posts.length
      }
    };

  } catch (error) {
    return {
      success: false,
      error: error.message,
      stack: error.stack
    };
  }
}
