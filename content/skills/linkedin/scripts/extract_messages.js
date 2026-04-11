/**
 * LinkedIn Messages Extractor
 *
 * Extracts message threads and conversation content.
 * NOTE: Messages contain private content - always show user before any vault operations.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on /messaging/ or a specific conversation
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on messaging
    if (!url.includes('/messaging')) {
      return {
        success: false,
        error: 'Not on LinkedIn messaging. Navigate to /messaging/'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    // Check if we're viewing a specific thread or the thread list
    const isThreadView = url.includes('/messaging/thread/');

    if (isThreadView) {
      // Extract messages from current thread
      const messages = [];

      // Get thread participant(s)
      const headerEl = document.querySelector('.msg-thread__link-to-profile, .msg-entity-lockup__entity-title');
      const threadWith = headerEl ? clean(headerEl.textContent) : '';

      // Get all messages in thread
      const messageEls = document.querySelectorAll('.msg-s-message-list__event, .msg-s-event-listitem');

      messageEls.forEach((msgEl, index) => {
        // Check if it's a message (not a system event)
        const contentEl = msgEl.querySelector('.msg-s-event-listitem__body, .msg-s-message-group__text');
        if (!contentEl) return;

        const content = clean(contentEl.textContent);
        if (!content) return;

        // Get sender
        const senderEl = msgEl.querySelector('.msg-s-message-group__name, .msg-s-event-listitem__name');
        const sender = senderEl ? clean(senderEl.textContent) : 'Unknown';

        // Get timestamp
        const timeEl = msgEl.querySelector('.msg-s-message-group__timestamp, time');
        const timestamp = timeEl ? clean(timeEl.textContent) : '';

        // Check if it's from me or them
        const isFromMe = msgEl.classList.contains('msg-s-event-listitem--from-me') ||
                         msgEl.closest('.msg-s-message-list--sent');

        messages.push({
          index: index + 1,
          sender: isFromMe ? 'Me' : sender,
          content: content.slice(0, 500), // Truncate long messages
          timestamp: timestamp,
          isFromMe: isFromMe
        });
      });

      return {
        success: true,
        viewType: 'thread',
        threadWith: threadWith,
        messageCount: messages.length,
        messages: messages.slice(0, 50), // Limit messages returned
        metadata: {
          url: url,
          extractedAt: new Date().toISOString(),
          note: 'Scroll up in thread to load older messages'
        },
        privacyNotice: 'Messages are private. User confirmation required before any vault operations.'
      };

    } else {
      // Extract thread list
      const threads = [];

      const threadEls = document.querySelectorAll('.msg-conversation-card, .msg-conversation-listitem');

      threadEls.forEach((threadEl, index) => {
        // Get participant name
        const nameEl = threadEl.querySelector('.msg-conversation-card__participant-names, .msg-conversation-listitem__participant-names');
        const participant = nameEl ? clean(nameEl.textContent) : '';

        // Get last message preview
        const previewEl = threadEl.querySelector('.msg-conversation-card__message-snippet, .msg-conversation-listitem__message-snippet');
        const preview = previewEl ? clean(previewEl.textContent) : '';

        // Get timestamp
        const timeEl = threadEl.querySelector('.msg-conversation-card__time-stamp, time');
        const timestamp = timeEl ? clean(timeEl.textContent) : '';

        // Get unread indicator
        const isUnread = threadEl.classList.contains('msg-conversation-card--unread') ||
                         threadEl.querySelector('.msg-conversation-card__unread-indicator') !== null;

        // Get thread URL
        const threadLink = threadEl.querySelector('a');
        const threadUrl = threadLink ? threadLink.href : '';

        if (participant) {
          threads.push({
            index: index + 1,
            participant: participant,
            preview: preview.slice(0, 100),
            timestamp: timestamp,
            isUnread: isUnread,
            threadUrl: threadUrl
          });
        }
      });

      return {
        success: true,
        viewType: 'list',
        threadCount: threads.length,
        threads: threads.slice(0, 30),
        metadata: {
          url: url,
          extractedAt: new Date().toISOString(),
          note: 'Click on a thread to view full conversation'
        },
        privacyNotice: 'Messages are private. User confirmation required before any vault operations.'
      };
    }

  } catch (error) {
    return {
      success: false,
      error: error.message,
      stack: error.stack
    };
  }
}
