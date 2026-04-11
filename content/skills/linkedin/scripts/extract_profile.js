/**
 * LinkedIn Profile Extractor (Feb 2026 DOM)
 *
 * Extracts profile data from a LinkedIn profile page.
 * Uses heading-based section discovery and innerText parsing.
 *
 * DOM Changes (Feb 2026):
 * - CSS classes are fully obfuscated (e.g. _92e46e58) — never match on class names
 * - h2 is used instead of h1 for profile names
 * - Section IDs (#about, #experience, #education, #skills) are gone
 * - .pvs-entity no longer exists
 * - aria-hidden spans no longer used for text
 *
 * Strategy: Find sections by h2 text content, parse innerText.
 * Supports both English and German section headings.
 *
 * Usage:
 *   playwright-cli -s=linkedin eval "$(cat scripts/extract_profile.js)"
 *
 * Prerequisites:
 * - Must be on a LinkedIn profile page (/in/{username}/)
 * - Page should be scrolled to load all sections before extraction
 */

() => {
  try {
    const url = window.location.href;

    // Verify we're on a profile page
    if (!url.includes('/in/')) {
      return {
        success: false,
        error: 'Not on a LinkedIn profile page. Expected URL containing /in/'
      };
    }

    // Extract username from URL
    const usernameMatch = url.match(/\/in\/([^\/\?]+)/);
    const username = usernameMatch ? usernameMatch[1] : '';

    // Get main content area
    const main = document.querySelector('main');
    if (!main) {
      return {
        success: false,
        error: 'Could not find main content area'
      };
    }

    // Helper to clean text
    const clean = (text) => text ? text.trim().replace(/\s+/g, ' ') : '';

    // --- Section discovery via h2 headings ---
    // Bilingual support: English / German
    const sectionHeadings = {
      about: ['About', 'Info', 'Über'],
      experience: ['Experience', 'Berufserfahrung'],
      education: ['Education', 'Ausbildung'],
      skills: ['Skills', 'Kenntnisse'],
      licenses: ['Licenses & certifications', 'Lizenzen und Zertifizierungen'],
      recommendations: ['Recommendations', 'Empfehlungen'],
    };

    function findSectionByHeading(headingVariants) {
      const h2s = Array.from(document.querySelectorAll('h2'));
      for (const heading of headingVariants) {
        const h2 = h2s.find(el => el.textContent.trim() === heading);
        if (h2) {
          // Walk up to find the parent <section>
          let parent = h2.parentElement;
          for (let i = 0; i < 6; i++) {
            if (parent && parent.tagName === 'SECTION') return parent;
            if (parent) parent = parent.parentElement;
          }
          return h2.closest('section') || parent;
        }
      }
      return null;
    }

    function getSectionText(headingVariants) {
      const section = findSectionByHeading(headingVariants);
      return section ? section.innerText : '';
    }

    // --- Header extraction from first <section> in main ---
    const firstSection = main.querySelector('section');
    const headerText = firstSection ? firstSection.innerText : '';
    const headerLines = headerText.split('\n').map(l => l.trim()).filter(Boolean);

    // Name is the first non-empty line
    const name = headerLines.length > 0 ? headerLines[0] : '';

    // Headline: skip "· 1st"/"· 2nd" line, take the next substantial text
    let headline = '';
    let location = '';
    let connectionInfo = '';
    let currentCompanyFromHeader = '';

    for (let i = 1; i < headerLines.length; i++) {
      const line = headerLines[i];
      if (line.startsWith('·') && line.length < 10) continue; // "· 1st" etc.
      if (line === '·') continue;
      if (line === 'Contact info' || line === 'Kontaktinfo') continue;
      if (line === 'Message' || line === 'Nachricht') break;

      if (!headline && line.length > 10) {
        headline = line;
      } else if (headline && !location && line.includes(',')) {
        // Location often contains a comma (city, region)
        location = line;
      } else if (line.includes('connections') || line.includes('Kontakte')) {
        connectionInfo = line;
      } else if (!currentCompanyFromHeader && !line.includes('mutual') && !line.includes('gemeinsam') && line.length > 2 && line.length < 80) {
        // Could be current company
        if (!location && !line.includes('connections')) {
          // If we haven't found location yet, this might be it
          if (line.includes(',') || line.match(/\b(Germany|Poland|US|UK|Remote)\b/i)) {
            location = line;
          } else {
            currentCompanyFromHeader = line;
          }
        }
      }
    }

    // --- About section ---
    const aboutText = getSectionText(sectionHeadings.about);
    const aboutLines = aboutText.split('\n').filter(l => l.trim());
    // Remove the "About" heading and "… more" suffix
    const about = aboutLines
      .slice(1) // skip "About" heading
      .filter(l => l.trim() !== '… more' && l.trim() !== '...mehr')
      .join('\n')
      .trim();

    // --- Experience section ---
    const experiences = [];
    const expText = getSectionText(sectionHeadings.experience);
    if (expText) {
      const expLines = expText.split('\n').map(l => l.trim()).filter(Boolean);
      // Skip the "Experience" heading
      let i = 1;
      while (i < expLines.length) {
        // Pattern: Title, Company · Type, Date range · Duration, [Location], [Description]
        const title = expLines[i] || '';
        const companyLine = expLines[i + 1] || '';
        const dateLine = expLines[i + 2] || '';

        // Check if this looks like an experience entry
        // Company line usually contains " · " (company · employment type)
        if (companyLine.includes(' · ') || dateLine.match(/\d{4}/)) {
          const exp = {
            title: title,
            company: companyLine,
            duration: dateLine
          };

          // Collect optional extra lines (location, description, skills)
          let j = i + 3;
          const extras = [];
          while (j < expLines.length) {
            const next = expLines[j];
            // Stop if we hit what looks like the next entry's title
            // (next line after this would be "Company · Type")
            if (j + 1 < expLines.length && expLines[j + 1].includes(' · ')) break;
            if (j + 2 < expLines.length && expLines[j + 2].match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|[A-Z][a-z]{2})\s+\d{4}/)) break;
            extras.push(next);
            j++;
          }

          if (extras.length > 0) {
            // First extra is often location (e.g. "Remote", "Berlin")
            if (extras[0].length < 40 && !extras[0].includes('skills')) {
              exp.location = extras[0];
              if (extras.length > 1) exp.description = extras.slice(1).join(' ');
            } else {
              exp.description = extras.join(' ');
            }
          }

          experiences.push(exp);
          i = j;
        } else {
          i++;
        }
      }
    }

    // --- Education section ---
    const education = [];
    const eduText = getSectionText(sectionHeadings.education);
    if (eduText) {
      const eduLines = eduText.split('\n').map(l => l.trim()).filter(Boolean);
      let i = 1; // skip heading
      while (i < eduLines.length) {
        const school = eduLines[i] || '';
        const degree = eduLines[i + 1] || '';
        const years = eduLines[i + 2] || '';

        if (school && school.length > 2) {
          education.push({
            school: school,
            degree: degree.match(/\d{4}/) ? '' : degree,
            years: degree.match(/\d{4}/) ? degree : years
          });
          i += degree.match(/\d{4}/) ? 2 : 3;
        } else {
          i++;
        }
      }
    }

    // --- Skills section ---
    const skills = [];
    const skillsText = getSectionText(sectionHeadings.skills);
    if (skillsText) {
      const skillLines = skillsText.split('\n').map(l => l.trim()).filter(Boolean);
      for (let i = 1; i < skillLines.length; i++) {
        const line = skillLines[i];
        // Skip lines that are endorsement context or buttons
        if (line === 'Endorse' || line === 'Bestätigen') continue;
        if (line === 'Show all' || line === 'Alle anzeigen') continue;
        if (line.includes(' at ') || line.includes(' bei ')) continue; // "Role at Company" context
        if (line.length > 0 && line.length < 50) {
          skills.push(line);
        }
      }
    }

    // Current company/role from experience or header
    let currentCompany = currentCompanyFromHeader;
    let currentRole = '';
    if (experiences.length > 0) {
      currentRole = experiences[0].title;
      if (!currentCompany) {
        currentCompany = experiences[0].company.split(' · ')[0];
      }
    }

    // Build result
    return {
      success: true,
      profile: {
        name: name,
        username: username,
        headline: headline,
        location: location,
        connectionInfo: connectionInfo,
        currentRole: currentRole,
        currentCompany: currentCompany,
        about: about,
        experienceCount: experiences.length,
        educationCount: education.length,
        skillsCount: skills.length
      },
      details: {
        experiences: experiences.slice(0, 10),
        education: education.slice(0, 5),
        skills: skills.slice(0, 20)
      },
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
