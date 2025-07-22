import React, { useEffect, useRef } from 'react';
import mermaid from 'mermaid';
import { DocumentationSection } from '../types';

interface DocumentationViewerProps {
  sections: DocumentationSection[];
  activeSection: string;
  title: string;
}

const DocumentationViewer: React.FC<DocumentationViewerProps> = ({
  sections,
  activeSection,
  title,
}) => {
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize Mermaid
    mermaid.initialize({
      startOnLoad: true,
      theme: 'default',
      securityLevel: 'loose',
    });

    // Render Mermaid diagrams
    if (contentRef.current) {
      const mermaidElements = contentRef.current.querySelectorAll('.mermaid');
      mermaidElements.forEach((element, index) => {
        const id = `mermaid-${Date.now()}-${index}`;
        element.id = id;
        mermaid.render(id, element.textContent || '', (svgCode) => {
          element.innerHTML = svgCode;
        });
      });
    }
  }, [sections, activeSection]);

  const renderContent = (content: string) => {
    // Split content into lines for processing
    const lines = content.split('\n');
    const elements: JSX.Element[] = [];
    let currentElement: string[] = [];
    let inCodeBlock = false;
    let inMermaidBlock = false;
    let codeLanguage = '';

    const flushCurrentElement = () => {
      if (currentElement.length > 0) {
        const text = currentElement.join('\n');
        if (text.trim()) {
          elements.push(
            <div
              key={elements.length}
              dangerouslySetInnerHTML={{ __html: parseMarkdown(text) }}
            />
          );
        }
        currentElement = [];
      }
    };

    lines.forEach((line, index) => {
      // Check for code block start/end
      if (line.startsWith('```')) {
        if (!inCodeBlock) {
          flushCurrentElement();
          inCodeBlock = true;
          codeLanguage = line.substring(3).trim();
          
          // Check if it's a mermaid diagram
          if (codeLanguage === 'mermaid') {
            inMermaidBlock = true;
            currentElement = [];
          } else {
            currentElement = [line];
          }
        } else {
          if (inMermaidBlock) {
            // Render mermaid diagram
            elements.push(
              <div key={elements.length} className="my-6">
                <div className="mermaid bg-white p-4 rounded-lg border border-gray-200">
                  {currentElement.join('\n')}
                </div>
              </div>
            );
            inMermaidBlock = false;
          } else {
            currentElement.push(line);
            elements.push(
              <pre key={elements.length} className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto my-4">
                <code className={`language-${codeLanguage}`}>
                  {currentElement.slice(1, -1).join('\n')}
                </code>
              </pre>
            );
          }
          inCodeBlock = false;
          currentElement = [];
        }
      } else {
        currentElement.push(line);
      }
    });

    // Flush any remaining content
    flushCurrentElement();

    return elements;
  };

  const parseMarkdown = (text: string): string => {
    return text
      // Headers (skip h1 as it's handled separately)
      .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-900 mt-6 mb-3">$1</h3>')
      .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-gray-900 mt-8 mb-4">$1</h2>')
      // Bold
      .replace(/\*\*(.*?)\*\*/gim, '<strong class="font-semibold">$1</strong>')
      // Italic
      .replace(/\*(.*?)\*/gim, '<em class="italic">$1</em>')
      // Inline code
      .replace(/`([^`]*)`/gim, '<code class="bg-gray-100 text-gray-800 px-1 py-0.5 rounded text-sm">$1</code>')
      // Links
      .replace(/\[([^\]]*)\]\(([^)]*)\)/gim, '<a href="$2" class="text-primary-600 hover:text-primary-700 underline" target="_blank" rel="noopener noreferrer">$1</a>')
      // Lists
      .replace(/^\* (.*$)/gim, '<li class="ml-4">• $1</li>')
      .replace(/^- (.*$)/gim, '<li class="ml-4">• $1</li>')
      // Line breaks
      .replace(/\n\n/gim, '</p><p class="mb-4">')
      .replace(/\n/gim, '<br>')
      // Wrap in paragraphs
      .replace(/^(?!<[h|l|p])/gim, '<p class="mb-4">')
      .replace(/(?<!>)$/gim, '</p>');
  };

  const activeSection_obj = sections.find(section => section.id === activeSection);

  if (!activeSection_obj) {
    return (
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="text-center py-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">{title}</h2>
            <p className="text-gray-600">Select a section from the sidebar to view the documentation.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 overflow-y-auto custom-scrollbar" id="documentation-content">
      <div className="max-w-4xl mx-auto" ref={contentRef}>
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{activeSection_obj.title}</h1>
          <div className="h-1 w-20 bg-primary-600 rounded"></div>
        </div>
        
        <div className="prose prose-lg max-w-none">
          {renderContent(activeSection_obj.content)}
        </div>
      </div>
    </div>
  );
};

export default DocumentationViewer;