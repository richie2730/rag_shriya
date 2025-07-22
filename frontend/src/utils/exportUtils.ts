import html2pdf from 'html2pdf.js';
import { saveAs } from 'file-saver';

export function exportToMarkdown(content: string, filename: string = 'documentation.md') {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
  saveAs(blob, filename);
}

export function exportToPDF(elementId: string, filename: string = 'documentation.pdf') {
  const element = document.getElementById(elementId);
  if (!element) return;

  const options = {
    margin: 1,
    filename: filename,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2, useCORS: true },
    jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
  };

  html2pdf().set(options).from(element).save();
}

export async function exportToWord(content: string, filename: string = 'documentation.docx') {
  try {
    // Convert markdown to HTML for better Word formatting
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>Documentation</title>
          <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; margin: 40px; }
            h1, h2, h3, h4, h5, h6 { color: #333; margin-top: 24px; margin-bottom: 16px; }
            h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; }
            h2 { border-bottom: 1px solid #eee; padding-bottom: 8px; }
            code { background-color: #f4f4f4; padding: 2px 4px; border-radius: 3px; }
            pre { background-color: #f8f8f8; padding: 16px; border-radius: 6px; overflow-x: auto; }
            blockquote { border-left: 4px solid #ddd; margin: 0; padding-left: 16px; color: #666; }
            table { border-collapse: collapse; width: 100%; margin: 16px 0; }
            th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
          </style>
        </head>
        <body>
          ${markdownToHtml(content)}
        </body>
      </html>
    `;

    // Create a simple Word-compatible HTML file
    const blob = new Blob([htmlContent], { 
      type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
    });
    saveAs(blob, filename);
  } catch (error) {
    console.error('Error exporting to Word:', error);
    // Fallback to HTML export
    const blob = new Blob([content], { type: 'text/html;charset=utf-8' });
    saveAs(blob, filename.replace('.docx', '.html'));
  }
}

function markdownToHtml(markdown: string): string {
  return markdown
    // Headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Bold
    .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*)\*/gim, '<em>$1</em>')
    // Code blocks
    .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]*)`/gim, '<code>$1</code>')
    // Line breaks
    .replace(/\n/gim, '<br>');
}