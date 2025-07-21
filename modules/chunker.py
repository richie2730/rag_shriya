from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


def load_and_split(repo_path: str, glob_pattern: str = "**/*.{py,java}"):
    """
    Load and split documents from a repository.

    Args:
        repo_path: Path to the repository
        glob_pattern: Glob pattern for file matching

    Returns:
        List of document chunks
    """
    loader = DirectoryLoader(repo_path, glob=glob_pattern, loader_cls=TextLoader)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(documents)
    print(f"[Chunker] Loaded {len(documents)} files and created {len(chunks)} chunks.")
    return chunks
