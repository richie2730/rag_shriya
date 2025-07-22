import React from 'react';
import { Loader2, FileText } from 'lucide-react';

interface LoadingSpinnerProps {
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  message = "Analyzing repository..." 
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <div className="relative">
        <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
          <FileText className="w-8 h-8 text-primary-600" />
        </div>
        <Loader2 className="w-6 h-6 text-primary-600 animate-spin absolute -top-1 -right-1" />
      </div>
      
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Processing Repository</h3>
      <p className="text-gray-600 text-center max-w-md">
        {message}
      </p>
      
      <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
        <div className="flex space-x-1">
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce"></div>
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
        </div>
        <span>This may take a few minutes</span>
      </div>
    </div>
  );
};

export default LoadingSpinner;