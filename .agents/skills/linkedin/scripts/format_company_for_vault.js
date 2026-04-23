/**
 * LinkedIn Company Formatter for Vault
 *
 * Formats LinkedIn company data for saving to Obsidian vault as an Organization note.
 * Takes company data from extract_company.js and outputs Obsidian-compatible markdown.
 *
 * Usage: Call this with company data extracted from extract_company.js
 */

(company, about, specialties) => {
  if (!company) {
    return {
      success: false,
      error: 'No company data provided'
    };
  }

  const today = new Date().toISOString().split('T')[0];

  // Build frontmatter
  const frontmatter = {
    name: company.name || '',
    aliases: [],
    type: 'organization',
    industry: company.industry || '',
    size: company.companySize || '',
    headquarters: company.headquarters || '',
    founded: company.founded || '',
    website: company.website || '',
    linkedin_url: company.url || `https://www.linkedin.com/company/${company.slug}/`,
    last_synced: today,
    tags: ['organization', 'linkedin']
  };

  // Build frontmatter YAML
  let yaml = '---\n';
  for (const [key, value] of Object.entries(frontmatter)) {
    if (Array.isArray(value)) {
      if (value.length === 0) {
        yaml += `${key}: []\n`;
      } else {
        yaml += `${key}:\n`;
        value.forEach(item => {
          yaml += `  - ${item}\n`;
        });
      }
    } else if (typeof value === 'string') {
      const escaped = value.replace(/"/g, '\\"');
      yaml += `${key}: "${escaped}"\n`;
    } else {
      yaml += `${key}: ${value}\n`;
    }
  }
  yaml += '---\n\n';

  // Build content
  let content = yaml;

  // Name as title
  content += `# ${company.name || 'Unknown Company'}\n\n`;

  // Tagline
  if (company.tagline) {
    content += `> ${company.tagline}\n\n`;
  }

  // Quick info table
  content += '## Overview\n\n';
  content += '| Field | Value |\n';
  content += '|-------|-------|\n';
  if (company.industry) content += `| Industry | ${company.industry} |\n`;
  if (company.companySize) content += `| Size | ${company.companySize} |\n`;
  if (company.headquarters) content += `| HQ | ${company.headquarters} |\n`;
  if (company.founded) content += `| Founded | ${company.founded} |\n`;
  if (company.followers) content += `| Followers | ${company.followers} |\n`;
  if (company.website) content += `| Website | ${company.website} |\n`;
  content += '\n';

  // About section
  if (about) {
    content += '## About\n\n';
    content += about + '\n\n';
  }

  // Specialties
  if (specialties) {
    content += '## Specialties\n\n';
    content += specialties + '\n\n';
  }

  // Known employees section (empty for user to link)
  content += '## Known Contacts\n\n';
  content += '<!-- Link People notes from this organization here -->\n\n';

  // Notes section
  content += '## Notes\n\n';
  content += '\n';

  // Generate suggested filename
  const nameSlug = (company.name || 'unknown')
    .replace(/[^a-zA-Z0-9\s]/g, '')
    .trim()
    .replace(/\s+/g, ' ');

  const suggestedFilename = `${nameSlug}.md`;

  return {
    success: true,
    markdown: content,
    suggestedFilename: suggestedFilename,
    suggestedPath: `50-Databases/Organizations/${suggestedFilename}`,
    metadata: {
      name: company.name,
      industry: company.industry,
      last_synced: today,
      linkedin_url: frontmatter.linkedin_url
    }
  };
}
