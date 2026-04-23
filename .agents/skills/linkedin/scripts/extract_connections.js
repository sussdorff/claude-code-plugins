/**
 * LinkedIn Connections List Extractor
 *
 * Extracts connections from the connections page.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on /mynetwork/invite-connect/connections/
 * - Scroll to load more connections before extraction
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on connections page
    if (!url.includes('/connections') && !url.includes('/mynetwork')) {
      return {
        success: false,
        error: 'Not on LinkedIn connections page'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    const connections = [];

    // Find connection cards
    const connectionCards = document.querySelectorAll('.mn-connection-card, .entity-result');

    connectionCards.forEach((card, index) => {
      // Extract name and profile URL
      const nameLink = card.querySelector('.mn-connection-card__link, .entity-result__title-text a');
      const name = nameLink ? clean(nameLink.textContent) : '';
      const profileUrl = nameLink ? nameLink.href : '';

      // Extract headline/occupation
      const headlineEl = card.querySelector('.mn-connection-card__occupation, .entity-result__primary-subtitle');
      const headline = headlineEl ? clean(headlineEl.textContent) : '';

      // Extract connected date if visible
      const dateEl = card.querySelector('.time-badge, .entity-result__secondary-subtitle');
      const connectedDate = dateEl ? clean(dateEl.textContent) : '';

      // Extract profile image URL (for deduplication)
      const imgEl = card.querySelector('img.presence-entity__image, img.entity-result__image');
      const imageUrl = imgEl ? imgEl.src : '';

      if (name) {
        connections.push({
          index: index + 1,
          name: name,
          headline: headline,
          profileUrl: profileUrl,
          connectedDate: connectedDate,
          imageUrl: imageUrl
        });
      }
    });

    // Get total connection count if visible
    const totalEl = document.querySelector('.mn-connections__header h1, .search-results__total');
    const totalText = totalEl ? clean(totalEl.textContent) : '';

    return {
      success: true,
      connectionCount: connections.length,
      connections: connections,
      metadata: {
        url: url,
        extractedAt: new Date().toISOString(),
        totalHeader: totalText,
        note: connections.length < 50 ? 'Scroll more to load additional connections' : ''
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
