"""
Simple test script to verify API is working
"""
import asyncio
import sys

async def test_imports():
    """Test that all modules can be imported"""
    try:
        print("Testing imports...")
        from models import Expert, ExpertCreate, ExpertType
        from storage import storage
        from seed import seed_legends
        from crew_agent import LegendAgentFactory
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

async def test_storage():
    """Test storage operations"""
    try:
        print("\nTesting storage...")
        from models import ExpertCreate, ExpertType
        from storage import storage
        
        # Test create expert
        expert_data = ExpertCreate(
            name="Test Expert",
            title="Test Title",
            expertise=["Test1", "Test2"],
            systemPrompt="Test prompt",
            expertType=ExpertType.CUSTOM
        )
        expert = await storage.create_expert(expert_data)
        print(f"✓ Created expert: {expert.name} ({expert.id})")
        
        # Test get expert
        retrieved = await storage.get_expert(expert.id)
        assert retrieved is not None
        print(f"✓ Retrieved expert: {retrieved.name}")
        
        # Test list experts
        experts = await storage.get_experts()
        print(f"✓ Listed {len(experts)} experts")
        
        return True
    except Exception as e:
        print(f"✗ Storage error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_seed():
    """Test seeding legends"""
    try:
        print("\nTesting seed...")
        from storage import MemStorage
        from seed import seed_legends
        
        test_storage = MemStorage()
        await seed_legends(test_storage)
        experts = await test_storage.get_experts()
        print(f"✓ Seeded {len(experts)} marketing legends")
        
        for expert in experts:
            print(f"  - {expert.name}: {expert.title}")
        
        return True
    except Exception as e:
        print(f"✗ Seed error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=" * 60)
    print("O Conselho Backend Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(await test_imports())
    results.append(await test_storage())
    results.append(await test_seed())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
