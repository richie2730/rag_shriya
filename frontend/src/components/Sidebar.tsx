import React from 'react';
import { X, FileText } from 'lucide-react';
import { DocumentationSection } from '../types';

interface SidebarProps {
  sections: DocumentationSection[];
  activeSection: string;
  onSectionClick: (sectionId: string) => void;
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  sections,
  activeSection,
  onSectionClick,
  isOpen,
  onClose,
}) => {
  const renderSections = (sections: DocumentationSection[], level = 0) => {
    return sections.map((section) => (
      <li key={section.id}>
        <button
          onClick={() => onSectionClick(section.id)}
          className={`sidebar-link w-full text-left ${
            activeSection === section.id ? 'active' : ''
          }`}
          style={{ paddingLeft: `${12 + level * 16}px` }}
        >
          <span className="truncate">{section.title}</span>
        </button>
      </li>
    ));
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed top-0 left-0 z-50 h-full w-80 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out lg:relative lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-primary-600" />
            <h2 className="font-semibold text-gray-900">Contents</h2>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <nav className="p-4 h-full overflow-y-auto custom-scrollbar">
          {sections.length > 0 ? (
            <ul className="space-y-1">
              {renderSections(sections)}
            </ul>
          ) : (
            <div className="text-center text-gray-500 mt-8">
              <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
              <p className="text-sm">No documentation sections available</p>
            </div>
          )}
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;