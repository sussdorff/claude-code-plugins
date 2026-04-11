/**
 * LinkedIn Post Formatter for Vault
 *
 * Formats a LinkedIn post for saving to Obsidian vault as a clipping/note.
 * Takes post data from extract_feed.js and outputs Obsidian-compatible markdown.
 *
 * Usage: Call this with post data extracted from extract_feed.js
 * This is a formatting helper, not a page extractor.
 */

(post) => {
  if (!post) {
    return {
      success: false,
      error: 'No post data provided'
    };
  }

  const today = new Date().toISOString().split('T')[0];

  // Build frontmatter
  const frontmatter = {
    type: 'clipping',
    source: 'LinkedIn',
    author: post.author || 'Unknown',
    author_headline: post.authorHeadline || '',
    captured: today,
    reactions: post.reactions || '0',
    comments: post.comments || '0',
    tags: ['linkedin', 'clipping']
  };

  // Build frontmatter YAML
  let yaml = '---\n';
  for (const [key, value] of Object.entries(frontmatter)) {
    if (Array.isArray(value)) {
      yaml += `${key}:\n`;
      value.forEach(item => {
        yaml += `  - ${item}\n`;
      });
    } else {
      yaml += `${key}: "${value}"\n`;
    }
  }
  yaml += '---\n\n';

  // Build content
  let content = yaml;

  // Title from first line of post or author
  const firstLine = post.content ? post.content.split('\n')[0].slice(0, 60) : 'LinkedIn Post';
  content += `# ${firstLine}${post.content && post.content.length > 60 ? '...' : ''}\n\n`;

  // Author info
  content += `**Author:** ${post.author || 'Unknown'}`;
  if (post.authorHeadline) {
    content += ` - ${post.authorHeadline}`;
  }
  content += '\n\n';

  // Timestamp
  if (post.timestamp) {
    content += `**Posted:** ${post.timestamp}\n\n`;
  }

  // Main content
  content += '## Content\n\n';
  content += post.content || '[No content extracted]';
  content += '\n\n';

  // Shared article if present
  if (post.sharedArticle) {
    content += '## Shared Article\n\n';
    if (post.sharedArticle.title) {
      content += `**${post.sharedArticle.title}**\n`;
    }
    if (post.sharedArticle.source) {
      content += `Source: ${post.sharedArticle.source}\n`;
    }
    content += '\n';
  }

  // Engagement metrics
  content += '## Engagement\n\n';
  content += `- Reactions: ${post.reactions || '0'}\n`;
  content += `- Comments: ${post.comments || '0'}\n`;
  if (post.reposts) {
    content += `- Reposts: ${post.reposts}\n`;
  }
  content += '\n';

  // Generate suggested filename
  const authorSlug = (post.author || 'unknown')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .slice(0, 30);
  const suggestedFilename = `${today}-linkedin-${authorSlug}.md`;

  return {
    success: true,
    markdown: content,
    suggestedFilename: suggestedFilename,
    suggestedPath: `00-Inbox/${suggestedFilename}`,
    metadata: {
      author: post.author,
      captured: today
    }
  };
}
