import { DocumentationSection, ParsedDocumentation } from '../types';

export function parseDocumentation(markdown: string): ParsedDocumentation {
  const lines = markdown.split('\n');
  const sections: DocumentationSection[] = [];
  let currentSection: DocumentationSection | null = null;
  let sectionCounter = 0;

  // Extract title from first heading
  const titleMatch = lines.find(line => line.startsWith('# '));
  const title = titleMatch ? titleMatch.replace('# ', '').trim() : 'Documentation';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // Check for headings
    const headingMatch = line.match(/^(#{1,6})\s+(.+)$/);
    
    if (headingMatch) {
      // Save previous section if exists
      if (currentSection) {
        sections.push(currentSection);
      }
      
      const level = headingMatch[1].length;
      const headingTitle = headingMatch[2].trim();
      
      // Skip the main title (level 1)
      if (level > 1) {
        sectionCounter++;
        currentSection = {
          id: `section-${sectionCounter}`,
          title: headingTitle,
          content: '',
          level: level - 1 // Adjust level since we skip h1
        };
      }
    } else if (currentSection) {
      // Add content to current section
      currentSection.content += line + '\n';
    }
  }
  
  // Add the last section
  if (currentSection) {
    sections.push(currentSection);
  }

  return {
    title,
    sections: sections.map(section => ({
      ...section,
      content: section.content.trim()
    }))
  };
}

export function generateTableOfContents(sections: DocumentationSection[]): DocumentationSection[] {
  return sections.filter(section => section.level <= 3); // Only show up to h3 in TOC
}