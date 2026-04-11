/**
 * LinkedIn Notifications Extractor
 *
 * Extracts notifications from the notifications page.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on /notifications/
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on notifications
    if (!url.includes('/notifications')) {
      return {
        success: false,
        error: 'Not on LinkedIn notifications. Navigate to /notifications/'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    const notifications = [];

    // Find notification cards
    const notifEls = document.querySelectorAll('.nt-card, .notification-card');

    notifEls.forEach((notifEl, index) => {
      // Get notification text
      const textEl = notifEl.querySelector('.nt-card__text, .notification-card__text');
      const text = textEl ? clean(textEl.textContent) : '';

      // Get timestamp
      const timeEl = notifEl.querySelector('.nt-card__time-ago, time');
      const timestamp = timeEl ? clean(timeEl.textContent) : '';

      // Get actor (person who triggered notification)
      const actorEl = notifEl.querySelector('.nt-card__actor-link, .notification-card__actor');
      const actor = actorEl ? clean(actorEl.textContent) : '';
      const actorUrl = actorEl?.href || '';

      // Determine notification type
      let type = 'unknown';
      const textLower = text.toLowerCase();
      if (textLower.includes('connection') || textLower.includes('connect with')) {
        type = 'connection';
      } else if (textLower.includes('liked') || textLower.includes('reaction')) {
        type = 'reaction';
      } else if (textLower.includes('commented')) {
        type = 'comment';
      } else if (textLower.includes('mentioned')) {
        type = 'mention';
      } else if (textLower.includes('job') || textLower.includes('hiring')) {
        type = 'job';
      } else if (textLower.includes('birthday')) {
        type = 'birthday';
      } else if (textLower.includes('anniversary') || textLower.includes('work anniversary')) {
        type = 'work_anniversary';
      } else if (textLower.includes('post') || textLower.includes('shared')) {
        type = 'post';
      } else if (textLower.includes('view') || textLower.includes('appeared')) {
        type = 'profile_view';
      }

      // Check if unread
      const isUnread = notifEl.classList.contains('nt-card--unread');

      if (text) {
        notifications.push({
          index: index + 1,
          type: type,
          text: text.slice(0, 200),
          timestamp: timestamp,
          actor: actor,
          actorUrl: actorUrl,
          isUnread: isUnread
        });
      }
    });

    // Group by type for summary
    const typeCounts = {};
    notifications.forEach(n => {
      typeCounts[n.type] = (typeCounts[n.type] || 0) + 1;
    });

    return {
      success: true,
      notificationCount: notifications.length,
      unreadCount: notifications.filter(n => n.isUnread).length,
      notifications: notifications.slice(0, 30),
      byType: typeCounts,
      metadata: {
        url: url,
        extractedAt: new Date().toISOString(),
        note: 'Scroll to load more notifications'
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
