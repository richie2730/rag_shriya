import React, { useState } from 'react';
import { FileText, Settings, Loader2 } from 'lucide-react';
import { FormData } from '../types';

interface DocumentationFormProps {
  onSubmit: (data: FormData) => void;
  isLoading: boolean;
}

const DocumentationForm: React.FC<DocumentationFormProps> = ({ onSubmit, isLoading }) => {
  const [formData, setFormData] = useState<FormData>({
    repoUrl: '',
    repoName: '',
    fileExtensions: '.py,.js,.ts,.java,.go',
    includeDiagrams: true,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center gap-3 mb-6">
        <FileText className="w-6 h-6 text-primary-600" />
        <h2 className="text-xl font-semibold text-gray-900">Generate Documentation</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="repoUrl" className="block text-sm font-medium text-gray-700 mb-2">
            GitHub Repository URL *
          </label>
          <input
            type="url"
            id="repoUrl"
            name="repoUrl"
            value={formData.repoUrl}
            onChange={handleInputChange}
            placeholder="https://github.com/username/repository.git"
            className="input-field"
            required
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Enter the full GitHub repository URL
          </p>
        </div>

        <div>
          <label htmlFor="repoName" className="block text-sm font-medium text-gray-700 mb-2">
            Repository Name
          </label>
          <input
            type="text"
            id="repoName"
            name="repoName"
            value={formData.repoName}
            onChange={handleInputChange}
            placeholder="my-awesome-project"
            className="input-field"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Optional: Custom name for the documentation
          </p>
        </div>

        <div>
          <label htmlFor="fileExtensions" className="block text-sm font-medium text-gray-700 mb-2">
            File Extensions
          </label>
          <input
            type="text"
            id="fileExtensions"
            name="fileExtensions"
            value={formData.fileExtensions}
            onChange={handleInputChange}
            placeholder=".py,.js,.ts,.java,.go"
            className="input-field"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Comma-separated list of file extensions to analyze
          </p>
        </div>

        <div className="flex items-center gap-3">
          <input
            type="checkbox"
            id="includeDiagrams"
            name="includeDiagrams"
            checked={formData.includeDiagrams}
            onChange={handleInputChange}
            className="w-4 h-4 text-primary-600 bg-gray-100 border-gray-300 rounded focus:ring-primary-500 focus:ring-2"
            disabled={isLoading}
          />
          <label htmlFor="includeDiagrams" className="text-sm font-medium text-gray-700">
            Include Diagrams
          </label>
          <Settings className="w-4 h-4 text-gray-400" />
        </div>

        <button
          type="submit"
          disabled={isLoading || !formData.repoUrl.trim()}
          className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Analyzing Repository...
            </>
          ) : (
            <>
              <FileText className="w-4 h-4" />
              Analyze Repository
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default DocumentationForm;