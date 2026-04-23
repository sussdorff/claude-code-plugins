/**
 * LinkedIn Profile Formatter for Vault
 *
 * Formats LinkedIn profile data for saving to Obsidian vault as a Contact note.
 * Matches the Contact.md template structure in 80-Templates/.
 *
 * Usage: Call this with profile data extracted from extract_profile.js
 * This is a formatting helper, not a page extractor.
 */

(profile, details, options = {}) => {
  if (!profile) {
    return {
      success: false,
      error: 'No profile data provided'
    };
  }

  const today = new Date().toISOString().split('T')[0];

  // Build frontmatter matching the Contact template (80-Templates/Contact.md)
  const frontmatter = {
    created: today,
    type: 'contact',
    name: profile.name || '',
    company: profile.currentCompany || '',
    role: profile.currentRole || '',
    linkedin_url: profile.url || '',
    email: options.email || '',
    phone: options.phone || '',
    location: profile.location || '',
    how_we_met: options.how_we_met || '',
    last_contact: options.last_contact || '',
    tags: ['linkedin']
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
      // Escape quotes in strings
      const escaped = value.replace(/"/g, '\\"');
      yaml += `${key}: "${escaped}"\n`;
    } else {
      yaml += `${key}: ${value}\n`;
    }
  }
  yaml += '---\n\n';

  // Build content
  let content = yaml;

  // Name as title (matching template: # <% tp.file.title %>)
  content += `# ${profile.name || 'Unknown'}\n\n`;

  // Headline as subtitle
  if (profile.headline) {
    content += `> ${profile.headline}\n\n`;
  }

  // About section (matching template structure)
  content += '## About\n';
  content += '<!-- Brief description of who they are and what they do -->\n\n';
  if (profile.about) {
    content += profile.about + '\n\n';
  }

  // Experience summary
  if (details && details.experiences && details.experiences.length > 0) {
    content += '**Experience:**\n';
    details.experiences.slice(0, 5).forEach(exp => {
      content += `- ${exp.title || 'Role'}`;
      if (exp.company) content += ` at ${exp.company}`;
      if (exp.duration) content += ` (${exp.duration})`;
      content += '\n';
    });
    content += '\n';
  }

  // Education summary
  if (details && details.education && details.education.length > 0) {
    content += '**Education:**\n';
    details.education.slice(0, 3).forEach(edu => {
      content += `- ${edu.school || 'School'}`;
      if (edu.degree) content += ` - ${edu.degree}`;
      if (edu.years) content += ` (${edu.years})`;
      content += '\n';
    });
    content += '\n';
  }

  // How We Know Each Other section (matching template)
  content += '\n## How We Know Each Other\n';
  content += '<!-- Context: where you met, who introduced you, shared projects -->\n\n';
  if (options.how_we_met) {
    content += options.how_we_met + '\n\n';
  }

  // Notes section (matching template)
  content += '\n## Notes\n';
  content += '<!-- Key things to remember about them -->\n\n';

  // Skills as tags/notes
  if (details && details.skills && details.skills.length > 0) {
    content += '**Skills:** ' + details.skills.slice(0, 10).join(', ') + '\n\n';
  }

  // Interactions section (matching template)
  content += '\n## Interactions\n';
  content += '<!-- Log of notable conversations, meetings, exchanges -->\n\n';

  // Generate suggested filename
  const nameSlug = (profile.name || 'unknown')
    .replace(/^(Dr\.|Prof\.|Mr\.|Ms\.|Mrs\.)\s*/i, '') // Remove titles
    .replace(/[^a-zA-Z0-9\s]/g, '') // Remove special chars
    .trim()
    .replace(/\s+/g, ' '); // Normalize spaces

  const suggestedFilename = `${nameSlug}.md`;

  return {
    success: true,
    markdown: content,
    suggestedFilename: suggestedFilename,
    suggestedPath: `50-Databases/Contacts/${suggestedFilename}`,
    metadata: {
      name: profile.name,
      company: profile.currentCompany,
      last_synced: today,
      linkedin_url: profile.url
    }
  };
}
