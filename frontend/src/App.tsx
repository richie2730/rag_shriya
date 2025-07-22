import React, { useState } from 'react';
import { Menu, AlertCircle } from 'lucide-react';
import Header from './components/Header';
import DocumentationForm from './components/DocumentationForm';
import Sidebar from './components/Sidebar';
import DocumentationViewer from './components/DocumentationViewer';
import ExportButtons from './components/ExportButtons';
import LoadingSpinner from './components/LoadingSpinner';
import { FormData, DocumentationResponse, ParsedDocumentation } from './types';
import { parseDocumentation } from './utils/documentationParser';
import { apiService } from './services/api';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [documentation, setDocumentation] = useState<ParsedDocumentation | null>(null);
  const [rawDocumentation, setRawDocumentation] = useState<string>('');
  const [activeSection, setActiveSection] = useState<string>('');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [repoName, setRepoName] = useState<string>('');

  const handleFormSubmit = async (formData: FormData) => {
    setIsLoading(true);
    setError(null);
    setDocumentation(null);
    setRawDocumentation('');

    try {
      // Parse file extensions
      const fileExtensions = formData.fileExtensions
        .split(',')
        .map(ext => ext.trim())
        .filter(ext => ext.length > 0);

      // Extract repo name from URL if not provided
      const extractedRepoName = formData.repoName || extractRepoNameFromUrl(formData.repoUrl);
      setRepoName(extractedRepoName);

      const requestData = {
        repo_url: formData.repoUrl,
        repo_name: extractedRepoName,
        include_diagrams: formData.includeDiagrams,
        file_extensions: fileExtensions,
        vector_db_provider: 'pinecone', // Default to pinecone
        llm_provider: 'gemini', // Default to gemini
      };

      const response: DocumentationResponse = await apiService.generateDocumentation(requestData);

      if (response.documentation) {
        const parsedDoc = parseDocumentation(response.documentation);
        setDocumentation(parsedDoc);
        setRawDocumentation(response.documentation);
        
        // Set first section as active
        if (parsedDoc.sections.length > 0) {
          setActiveSection(parsedDoc.sections[0].id);
        }
      } else {
        throw new Error('No documentation was generated');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An unexpected error occurred';
      setError(errorMessage);
      console.error('Documentation generation failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const extractRepoNameFromUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      const pathParts = urlObj.pathname.split('/').filter(part => part.length > 0);
      if (pathParts.length >= 2) {
        let repoName = pathParts[pathParts.length - 1];
        if (repoName.endsWith('.git')) {
          repoName = repoName.slice(0, -4);
        }
        return repoName;
      }
    } catch (e) {
      // If URL parsing fails, return a default name
    }
    return 'repository';
  };

  const handleSectionClick = (sectionId: string) => {
    setActiveSection(sectionId);
    setSidebarOpen(false); // Close sidebar on mobile after selection
  };

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <div className="max-w-7xl mx-auto px-6 py-8">
        {!documentation && !isLoading && (
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-4">
                AI-Powered Code Documentation
              </h1>
              <p className="text-lg text-gray-600">
                Generate comprehensive technical documentation for any GitHub repository using advanced AI analysis.
              </p>
            </div>
            
            <DocumentationForm onSubmit={handleFormSubmit} isLoading={isLoading} />
            
            {error && (
              <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="text-sm font-medium text-red-800">Error</h3>
                    <p className="text-sm text-red-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {isLoading && (
          <div className="max-w-2xl mx-auto">
            <LoadingSpinner message="Analyzing repository and generating documentation..." />
          </div>
        )}

        {documentation && !isLoading && (
          <div className="flex gap-6 min-h-screen">
            {/* Mobile menu button */}
            <button
              onClick={toggleSidebar}
              className="lg:hidden fixed top-20 left-4 z-30 bg-white p-2 rounded-lg shadow-md border border-gray-200"
            >
              <Menu className="w-5 h-5 text-gray-600" />
            </button>

            {/* Sidebar */}
            <Sidebar
              sections={documentation.sections}
              activeSection={activeSection}
              onSectionClick={handleSectionClick}
              isOpen={sidebarOpen}
              onClose={() => setSidebarOpen(false)}
            />

            {/* Main content */}
            <div className="flex-1 flex flex-col min-h-screen lg:ml-0">
              <DocumentationViewer
                sections={documentation.sections}
                activeSection={activeSection}
                title={documentation.title}
              />
              
              <ExportButtons
                documentation={rawDocumentation}
                repoName={repoName}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;