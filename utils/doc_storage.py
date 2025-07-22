"""
Documentation storage utilities.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class DocumentationStorage:
    """Handle storage and retrieval of generated documentation."""

    def __init__(self, base_directory: str = "./docs"):
        """
        Initialize documentation storage.

        Args:
            base_directory: Base directory for storing documentation
        """
        self.base_dir = Path(base_directory)
        self.repos_dir = self.base_dir / "repositories"
        self.metadata_dir = self.base_dir / "metadata"
        
        # Ensure directories exist
        self.repos_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def save_documentation(
        self, 
        repo_name: str, 
        documentation: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Save documentation and metadata to files.

        Args:
            repo_name: Repository name
            documentation: Documentation content
            metadata: Metadata about the documentation

        Returns:
            Dict with file paths
        """
        try:
            # Generate timestamp for unique filenames
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create filenames
            doc_filename = f"{repo_name}_{timestamp}.md"
            metadata_filename = f"{repo_name}_{timestamp}_metadata.json"
            
            # File paths
            doc_path = self.repos_dir / doc_filename
            metadata_path = self.metadata_dir / metadata_filename
            
            # Add file information to metadata
            metadata.update({
                "generated_at": datetime.now().isoformat(),
                "documentation_file": doc_filename,
                "file_size": len(documentation.encode('utf-8')),
                "doc_path": str(doc_path.absolute())
            })
            
            # Save documentation
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(documentation)
            
            # Save metadata
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, default=str)
            
            # Update latest symlink
            self._update_latest_link(repo_name, doc_filename)
            
            logger.info(f"Saved documentation: {doc_path}")
            logger.info(f"Saved metadata: {metadata_path}")
            
            return {
                "doc_file": str(doc_path),
                "metadata_file": str(metadata_path),
                "doc_filename": doc_filename,
                "metadata_filename": metadata_filename
            }
            
        except Exception as e:
            logger.error(f"Failed to save documentation for {repo_name}: {str(e)}")
            raise

    def get_documentation_by_repo(self, repo_name: str) -> Optional[str]:
        """
        Get the latest documentation for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Documentation content or None if not found
        """
        try:
            # Check for latest symlink first
            latest_link = self.repos_dir / f"{repo_name}_latest.md"
            
            if latest_link.exists():
                # Read the symlink target
                with open(latest_link, 'r', encoding='utf-8') as f:
                    target_filename = f.read().strip()
                
                target_path = self.repos_dir / target_filename
                if target_path.exists():
                    with open(target_path, 'r', encoding='utf-8') as f:
                        return f.read()
            
            # Fallback: find the most recent file
            pattern = f"{repo_name}_*.md"
            matching_files = list(self.repos_dir.glob(pattern))
            
            if not matching_files:
                return None
            
            # Sort by modification time (most recent first)
            latest_file = max(matching_files, key=lambda p: p.stat().st_mtime)
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to get documentation for {repo_name}: {str(e)}")
            return None

    def get_documentation_list(self) -> List[Dict[str, Any]]:
        """
        Get list of all documentation with metadata.

        Returns:
            List of documentation metadata
        """
        try:
            docs_list = []
            
            # Get all metadata files
            metadata_files = list(self.metadata_dir.glob("*_metadata.json"))
            
            for metadata_file in metadata_files:
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Add file path information
                    metadata["metadata_file_path"] = str(metadata_file)
                    
                    docs_list.append(metadata)
                    
                except Exception as e:
                    logger.warning(f"Failed to read metadata file {metadata_file}: {str(e)}")
                    continue
            
            # Sort by generation time (most recent first)
            docs_list.sort(
                key=lambda x: x.get("generated_at", ""), 
                reverse=True
            )
            
            return docs_list
            
        except Exception as e:
            logger.error(f"Failed to get documentation list: {str(e)}")
            return []

    def cleanup_old_files(self, keep_versions: int = 3) -> int:
        """
        Clean up old documentation files, keeping only recent versions.

        Args:
            keep_versions: Number of versions to keep per repository

        Returns:
            Number of files cleaned up
        """
        try:
            cleaned_count = 0
            
            # Group files by repository name
            repo_files = {}
            
            # Process documentation files
            for doc_file in self.repos_dir.glob("*.md"):
                if doc_file.name.endswith("_latest.md"):
                    continue  # Skip latest symlinks
                
                # Extract repo name (everything before the last underscore and timestamp)
                name_parts = doc_file.stem.split("_")
                if len(name_parts) >= 3:  # repo_name_timestamp format
                    repo_name = "_".join(name_parts[:-2])  # Everything except last 2 parts
                    
                    if repo_name not in repo_files:
                        repo_files[repo_name] = []
                    
                    repo_files[repo_name].append(doc_file)
            
            # Clean up old files for each repository
            for repo_name, files in repo_files.items():
                if len(files) > keep_versions:
                    # Sort by modification time (newest first)
                    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                    
                    # Remove old files
                    for old_file in files[keep_versions:]:
                        try:
                            # Remove documentation file
                            old_file.unlink()
                            cleaned_count += 1
                            
                            # Remove corresponding metadata file
                            metadata_file = self.metadata_dir / f"{old_file.stem}_metadata.json"
                            if metadata_file.exists():
                                metadata_file.unlink()
                                cleaned_count += 1
                            
                            logger.info(f"Cleaned up old files for {repo_name}: {old_file.name}")
                            
                        except Exception as e:
                            logger.warning(f"Failed to cleanup file {old_file}: {str(e)}")
                            continue
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
            return 0

    def _update_latest_link(self, repo_name: str, doc_filename: str) -> None:
        """
        Update the latest documentation link for a repository.

        Args:
            repo_name: Repository name
            doc_filename: Documentation filename
        """
        try:
            latest_link = self.repos_dir / f"{repo_name}_latest.md"
            
            # Write the target filename to the "symlink" file
            with open(latest_link, 'w', encoding='utf-8') as f:
                f.write(doc_filename)
            
            logger.debug(f"Updated latest link for {repo_name}: {doc_filename}")
            
        except Exception as e:
            logger.warning(f"Failed to update latest link for {repo_name}: {str(e)}")

    def get_repository_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored documentation.

        Returns:
            Dictionary with statistics
        """
        try:
            stats = {
                "total_repositories": 0,
                "total_documents": 0,
                "total_size_mb": 0.0,
                "repositories": {}
            }
            
            # Count documentation files
            doc_files = list(self.repos_dir.glob("*.md"))
            doc_files = [f for f in doc_files if not f.name.endswith("_latest.md")]
            
            stats["total_documents"] = len(doc_files)
            
            # Group by repository and calculate sizes
            repo_counts = {}
            total_size = 0
            
            for doc_file in doc_files:
                # Extract repo name
                name_parts = doc_file.stem.split("_")
                if len(name_parts) >= 3:
                    repo_name = "_".join(name_parts[:-2])
                    
                    if repo_name not in repo_counts:
                        repo_counts[repo_name] = 0
                    
                    repo_counts[repo_name] += 1
                    
                    # Add file size
                    try:
                        file_size = doc_file.stat().st_size
                        total_size += file_size
                    except OSError:
                        pass
            
            stats["total_repositories"] = len(repo_counts)
            stats["total_size_mb"] = total_size / (1024 * 1024)
            stats["repositories"] = repo_counts
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get repository stats: {str(e)}")
            return {}