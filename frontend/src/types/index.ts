export interface DocumentationRequest {
  repo_url: string;
  repo_name?: string;
  include_diagrams: boolean;
  file_extensions: string[];
  vector_db_provider?: string;
  llm_provider?: string;
}

export interface DocumentationResponse {
  task_id: string;
  status: string;
  message: string;
  documentation?: string;
  repo_name?: string;
  processing_time?: number;
  doc_file_path?: string;
  storage_info?: {
    doc_file: string;
    metadata_file: string;
  };
}

export interface DocumentationSection {
  id: string;
  title: string;
  content: string;
  level: number;
}

export interface ParsedDocumentation {
  title: string;
  sections: DocumentationSection[];
}

export interface FormData {
  repoUrl: string;
  repoName: string;
  fileExtensions: string;
  includeDiagrams: boolean;
}