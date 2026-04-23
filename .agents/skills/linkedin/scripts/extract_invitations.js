/**
 * LinkedIn Invitations Extractor
 *
 * Extracts pending invitations (sent and received).
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on /mynetwork/invitation-manager/
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on invitations page
    if (!url.includes('/invitation-manager')) {
      return {
        success: false,
        error: 'Not on LinkedIn invitations page. Navigate to /mynetwork/invitation-manager/'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    const received = [];
    const sent = [];

    // Check which tab we're on
    const isReceivedTab = url.includes('invitationType=CONNECTION') || !url.includes('invitationType=');
    const isSentTab = url.includes('invitationType=SENT');

    // Find invitation cards
    const invitationCards = document.querySelectorAll('.invitation-card, .invitation-card__item');

    invitationCards.forEach((card, index) => {
      // Extract name and profile
      const nameLink = card.querySelector('.invitation-card__title a, .invitation-card__name');
      const name = nameLink ? clean(nameLink.textContent) : '';
      const profileUrl = nameLink?.href || '';

      // Extract headline
      const headlineEl = card.querySelector('.invitation-card__subtitle, .invitation-card__occupation');
      const headline = headlineEl ? clean(headlineEl.textContent) : '';

      // Extract mutual connections
      const mutualEl = card.querySelector('.invitation-card__common-connections');
      const mutual = mutualEl ? clean(mutualEl.textContent) : '';

      // Extract time sent
      const timeEl = card.querySelector('.time-badge, .invitation-card__time');
      const time = timeEl ? clean(timeEl.textContent) : '';

      // Extract message if any
      const messageEl = card.querySelector('.invitation-card__message');
      const message = messageEl ? clean(messageEl.textContent) : '';

      if (name) {
        const invitation = {
          index: index + 1,
          name: name,
          headline: headline,
          profileUrl: profileUrl,
          mutualConnections: mutual,
          time: time,
          message: message
        };

        if (isSentTab) {
          sent.push(invitation);
        } else {
          received.push(invitation);
        }
      }
    });

    return {
      success: true,
      currentTab: isSentTab ? 'sent' : 'received',
      receivedCount: received.length,
      sentCount: sent.length,
      received: received,
      sent: sent,
      metadata: {
        url: url,
        extractedAt: new Date().toISOString(),
        note: 'Switch tabs using URL param: invitationType=SENT or invitationType=CONNECTION'
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
