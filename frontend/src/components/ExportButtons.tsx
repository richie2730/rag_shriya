import React from 'react';
import { Download, FileText, File, FileImage } from 'lucide-react';
import { exportToMarkdown, exportToPDF, exportToWord } from '../utils/exportUtils';

interface ExportButtonsProps {
  documentation: string;
  repoName: string;
}

const ExportButtons: React.FC<ExportButtonsProps> = ({ documentation, repoName }) => {
  const baseFilename = repoName ? `${repoName}-documentation` : 'documentation';

  const handleExportMarkdown = () => {
    exportToMarkdown(documentation, `${baseFilename}.md`);
  };

  const handleExportPDF = () => {
    exportToPDF('documentation-content', `${baseFilename}.pdf`);
  };

  const handleExportWord = () => {
    exportToWord(documentation, `${baseFilename}.docx`);
  };

  return (
    <div className="bg-white border-t border-gray-200 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center gap-3 mb-4">
          <Download className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Export Documentation</h3>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={handleExportMarkdown}
            className="btn-secondary flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            Export to Markdown
          </button>
          
          <button
            onClick={handleExportPDF}
            className="btn-secondary flex items-center gap-2"
          >
            <FileImage className="w-4 h-4" />
            Export to PDF
          </button>
          
          <button
            onClick={handleExportWord}
            className="btn-secondary flex items-center gap-2"
          >
            <File className="w-4 h-4" />
            Export to Word
          </button>
        </div>
        
        <p className="text-sm text-gray-500 mt-3">
          Choose your preferred format to download the documentation.
        </p>
      </div>
    </div>
  );
};

export default ExportButtons;