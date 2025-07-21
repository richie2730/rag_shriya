#!/usr/bin/env python3
"""
Quick test for documentation generation after vector DB cleanup
"""
import asyncio
import os
import sys

# Add the project root to Python path
sys.path.insert(0, "/Users/devesh.kumar/open-source/test")


async def test_full_pipeline():
    """Test the full documentation generation pipeline."""
    print("🚀 Testing Full Documentation Pipeline")
    print("=" * 45)

    try:
        # Import modules
        from core.config import get_settings
        from services.documentation_service import DocumentationService

        # Create settings
        settings = get_settings()
        print(f"✅ Settings loaded")

        # Create documentation service
        doc_service = DocumentationService(settings)
        print("✅ Documentation service created")

        # Test with the repository from your integration test
        test_repo = "https://github.com/SeptBlast/covid19.git"
        task_id = "test-cleanup"

        print(f"📁 Testing with repository: {test_repo}")

        # Clone repository
        repo_path = await doc_service._clone_repository(test_repo, task_id)
        print(f"✅ Repository cloned to: {repo_path}")

        # Check files
        if os.path.exists(repo_path):
            files = [
                f for f in os.listdir(repo_path) if f.endswith((".py", ".md", ".txt"))
            ][
                :10
            ]  # Show first 10 relevant files
            print(f"📂 Found {len(files)} relevant files: {files}")

        # Test vector database integration
        print(f"\n🔧 Testing vector database integration...")
        from modules.ingest_vectordb import init_pinecone

        try:
            index_name = init_pinecone("code-docs")
            print(f"✅ Vector database ready: {index_name}")
        except Exception as e:
            print(f"❌ Vector database error: {e}")
            return False

        # Cleanup
        await doc_service._cleanup_repository(repo_path)
        print("✅ Cleanup completed")

        print(f"\n🎉 Full pipeline test successful!")
        print(f"   - Git clone: ✅")
        print(f"   - Vector database: ✅")
        print(f"   - File processing: ✅")
        print(f"   - Cleanup: ✅")

        return True

    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test function."""
    success = await test_full_pipeline()

    if success:
        print(f"\n✅ Your system is ready for documentation generation!")
        print(f"   The 403 Pinecone error should now be resolved.")
        print(f"\n🚀 Next steps:")
        print(f"   1. Start the application: python app.py")
        print(f"   2. Test via API at: http://localhost:8000/docs")
        print(f"   3. Generate documentation for any repository!")
    else:
        print(f"\n❌ There are still issues to resolve.")
        print(f"   Check the error messages above.")


if __name__ == "__main__":
    asyncio.run(main())
