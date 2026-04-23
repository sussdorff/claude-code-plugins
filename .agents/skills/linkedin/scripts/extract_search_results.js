/**
 * LinkedIn Search Results Extractor
 *
 * Extracts people/company search results from LinkedIn.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on LinkedIn search results page (/search/results/...)
 * - Should scroll to load more results before extraction
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on search results
    if (!url.includes('/search/results')) {
      return {
        success: false,
        error: 'Not on LinkedIn search results. Expected URL containing /search/results'
      };
    }

    // Determine search type
    const searchType = url.includes('/people/') ? 'people' :
                       url.includes('/companies/') ? 'companies' :
                       url.includes('/all/') ? 'all' : 'unknown';

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    const results = [];

    if (searchType === 'people' || searchType === 'all') {
      // Extract people results
      const peopleResults = document.querySelectorAll('.entity-result, .reusable-search__result-container');

      peopleResults.forEach((resultEl, index) => {
        // Extract name and profile link
        const nameLink = resultEl.querySelector('.entity-result__title-text a, .app-aware-link');
        const name = nameLink ? clean(nameLink.textContent) : '';
        const profileUrl = nameLink ? nameLink.href : '';

        // Extract headline
        const headlineEl = resultEl.querySelector('.entity-result__primary-subtitle, .entity-result__summary');
        const headline = headlineEl ? clean(headlineEl.textContent) : '';

        // Extract location
        const locationEl = resultEl.querySelector('.entity-result__secondary-subtitle');
        const location = locationEl ? clean(locationEl.textContent) : '';

        // Extract connection degree
        const degreeEl = resultEl.querySelector('.entity-result__badge-text');
        const degree = degreeEl ? clean(degreeEl.textContent) : '';

        // Extract mutual connections
        const mutualEl = resultEl.querySelector('.entity-result__simple-insight');
        const mutual = mutualEl ? clean(mutualEl.textContent) : '';

        if (name) {
          results.push({
            type: 'person',
            index: index + 1,
            name: name,
            headline: headline,
            location: location,
            connectionDegree: degree,
            mutualConnections: mutual,
            profileUrl: profileUrl
          });
        }
      });
    }

    if (searchType === 'companies' || searchType === 'all') {
      // Extract company results
      const companyResults = document.querySelectorAll('.entity-result--company');

      companyResults.forEach((resultEl, index) => {
        const nameLink = resultEl.querySelector('.entity-result__title-text a');
        const name = nameLink ? clean(nameLink.textContent) : '';
        const companyUrl = nameLink ? nameLink.href : '';

        const industryEl = resultEl.querySelector('.entity-result__primary-subtitle');
        const industry = industryEl ? clean(industryEl.textContent) : '';

        const followersEl = resultEl.querySelector('.entity-result__secondary-subtitle');
        const followers = followersEl ? clean(followersEl.textContent) : '';

        if (name) {
          results.push({
            type: 'company',
            index: results.length + 1,
            name: name,
            industry: industry,
            followers: followers,
            companyUrl: companyUrl
          });
        }
      });
    }

    // Extract search metadata
    const resultsCountEl = document.querySelector('.search-results-container h2, .pb2.t-black--light');
    const resultsCountText = resultsCountEl ? clean(resultsCountEl.textContent) : '';

    return {
      success: true,
      searchType: searchType,
      resultCount: results.length,
      results: results.slice(0, 25), // Limit results
      metadata: {
        url: url,
        extractedAt: new Date().toISOString(),
        resultsHeader: resultsCountText
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
