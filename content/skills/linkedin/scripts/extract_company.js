/**
 * LinkedIn Company Page Extractor
 *
 * Extracts company data from a LinkedIn company page.
 *
 * Usage in Claude in Chrome MCP:
 * mcp__claude-in-chrome__javascript_tool with this function as arrow function
 *
 * Prerequisites:
 * - Must be on a LinkedIn company page (/company/{slug}/)
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on a company page
    if (!url.includes('/company/')) {
      return {
        success: false,
        error: 'Not on a LinkedIn company page. Expected URL containing /company/'
      };
    }

    // Extract slug from URL
    const slugMatch = url.match(/\/company\/([^\/\?]+)/);
    const slug = slugMatch ? slugMatch[1] : '';

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    // Extract company name
    const nameEl = document.querySelector('h1');
    const name = nameEl ? clean(nameEl.textContent) : '';

    // Extract tagline/headline
    const taglineEl = document.querySelector('.org-top-card-summary__tagline');
    const tagline = taglineEl ? clean(taglineEl.textContent) : '';

    // Extract industry and company info from the info section
    let industry = '';
    let companySize = '';
    let headquarters = '';
    let founded = '';
    let specialties = '';

    // Try to find the "About" section data
    const infoItems = document.querySelectorAll('.org-page-details__definition-term');
    infoItems.forEach(item => {
      const label = clean(item.textContent).toLowerCase();
      const valueEl = item.nextElementSibling;
      const value = valueEl ? clean(valueEl.textContent) : '';

      if (label.includes('industry')) industry = value;
      else if (label.includes('company size')) companySize = value;
      else if (label.includes('headquarters')) headquarters = value;
      else if (label.includes('founded')) founded = value;
      else if (label.includes('specialties')) specialties = value;
    });

    // Fallback: Try the summary info line
    const summaryEl = document.querySelector('.org-top-card-summary-info-list');
    if (summaryEl) {
      const summaryText = clean(summaryEl.textContent);
      // Extract from format like "Software Development · 51-200 employees · San Francisco"
      const parts = summaryText.split('·').map(p => p.trim());
      if (parts.length >= 1 && !industry) industry = parts[0];
      if (parts.length >= 2 && !companySize) companySize = parts[1];
      if (parts.length >= 3 && !headquarters) headquarters = parts[2];
    }

    // Extract follower count
    const followersEl = document.querySelector('.org-top-card-summary__follower-count');
    const followers = followersEl ? clean(followersEl.textContent) : '';

    // Extract "About" text
    const aboutEl = document.querySelector('.org-page-details__definition-text, .org-about-company-module__description');
    const about = aboutEl ? clean(aboutEl.textContent) : '';

    // Extract website
    const websiteEl = document.querySelector('a[data-control-name="top_card_website"], .org-top-card-primary-actions a[href*="http"]');
    const website = websiteEl ? websiteEl.href : '';

    // Employee count from link
    const employeesLink = document.querySelector('a[href*="/company/' + slug + '/people/"]');
    const employeesText = employeesLink ? clean(employeesLink.textContent) : '';

    return {
      success: true,
      company: {
        name: name,
        slug: slug,
        tagline: tagline,
        industry: industry,
        companySize: companySize,
        headquarters: headquarters,
        founded: founded,
        followers: followers,
        website: website,
        employeesOnLinkedIn: employeesText
      },
      about: about,
      specialties: specialties,
      metadata: {
        url: url,
        extractedAt: new Date().toISOString()
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
