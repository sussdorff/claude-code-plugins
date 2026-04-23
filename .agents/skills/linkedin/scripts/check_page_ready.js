/**
 * LinkedIn Page Ready Check
 *
 * Checks if a LinkedIn page has finished loading dynamic content.
 * Use before extraction to ensure content is available.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 */

() => {
  try {
    // Check for LinkedIn loading indicators
    const loadingSpinner = document.querySelector('.artdeco-loader, .loading-icon, [class*="loading"]');
    const isLoading = loadingSpinner && loadingSpinner.offsetParent !== null;

    // Check for skeleton/placeholder content
    const skeletons = document.querySelectorAll('.skeleton-loader, .ghost-loader, [class*="skeleton"]');
    const hasSkeletons = skeletons.length > 0;

    // Check for main content area
    const hasMainContent = document.querySelector('main') !== null;

    // Check for profile-specific content
    const isProfilePage = window.location.href.includes('/in/');
    let profileReady = true;
    if (isProfilePage) {
      profileReady = document.querySelector('h1') !== null &&
                     document.querySelector('.text-body-medium') !== null;
    }

    // Check for feed-specific content
    const isFeedPage = window.location.href.includes('/feed');
    let feedReady = true;
    if (isFeedPage) {
      feedReady = document.querySelector('.scaffold-finite-scroll__content') !== null;
    }

    // Check for search-specific content
    const isSearchPage = window.location.href.includes('/search/results');
    let searchReady = true;
    if (isSearchPage) {
      searchReady = document.querySelector('.entity-result, .reusable-search__result-container') !== null;
    }

    const isReady = !isLoading && !hasSkeletons && hasMainContent &&
                    profileReady && feedReady && searchReady;

    return {
      success: true,
      ready: isReady,
      details: {
        isLoading: isLoading,
        hasSkeletons: hasSkeletons,
        hasMainContent: hasMainContent,
        profileReady: isProfilePage ? profileReady : null,
        feedReady: isFeedPage ? feedReady : null,
        searchReady: isSearchPage ? searchReady : null
      },
      pageType: isProfilePage ? 'profile' :
                isFeedPage ? 'feed' :
                isSearchPage ? 'search' : 'other',
      recommendation: isReady ? 'Page ready for extraction' :
                      isLoading ? 'Wait 2-3 seconds for loading to complete' :
                      hasSkeletons ? 'Wait 1-2 seconds for content placeholders to load' :
                      'Scroll to load more content or verify you are on the correct page'
    };

  } catch (error) {
    return {
      success: false,
      error: error.message
    };
  }
}
