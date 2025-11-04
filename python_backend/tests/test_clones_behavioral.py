"""
Behavioral Tests for Marketing Legend Cognitive Clones.

Validates Framework EXTRACT de 20 Pontos implementation:
- Story banks (5+ per clone)
- Iconic callbacks (7+ per clone)
- Triggers (30+ per clone: 15 positive + 15 negative)
- Trigger reactions (5+ per clone)
- System prompt quality (350+ lines per clone)
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from clones.registry import CloneRegistry


class CloneBehavioralTester:
    """Test suite for cognitive clone behavioral validation."""
    
    def __init__(self):
        self.registry = CloneRegistry()
        self.results = {
            "total_clones": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def run_all_tests(self) -> dict:
        """Run all behavioral tests on all registered clones."""
        print("🧪 Starting Behavioral Tests for Cognitive Clones\n")
        print("=" * 70)
        
        clones_dict = self.registry.get_all_clones()
        self.results["total_clones"] = len(clones_dict)
        
        for clone_name, clone in clones_dict.items():
            print(f"\n📋 Testing: {clone.name}")
            print("-" * 70)
            
            clone_passed = True
            
            # Test 1: Story Banks (minimum 5)
            story_count = len(clone.story_banks)
            if story_count >= 5:
                print(f"  ✅ Story banks: {story_count} (target: 5+)")
            else:
                print(f"  ❌ Story banks: {story_count} (target: 5+)")
                self.results["errors"].append(f"{clone.name}: Insufficient story banks ({story_count})")
                clone_passed = False
            
            # Test 2: Iconic Callbacks (minimum 7)
            callback_count = len(clone.iconic_callbacks)
            if callback_count >= 7:
                print(f"  ✅ Iconic callbacks: {callback_count} (target: 7+)")
            else:
                print(f"  ❌ Iconic callbacks: {callback_count} (target: 7+)")
                self.results["errors"].append(f"{clone.name}: Insufficient callbacks ({callback_count})")
                clone_passed = False
            
            # Test 3: Positive Triggers (minimum 15)
            pos_trigger_count = len(clone.positive_triggers)
            if pos_trigger_count >= 15:
                print(f"  ✅ Positive triggers: {pos_trigger_count} (target: 15+)")
            else:
                print(f"  ❌ Positive triggers: {pos_trigger_count} (target: 15+)")
                self.results["errors"].append(f"{clone.name}: Insufficient positive triggers ({pos_trigger_count})")
                clone_passed = False
            
            # Test 4: Negative Triggers (minimum 15)
            neg_trigger_count = len(clone.negative_triggers)
            if neg_trigger_count >= 15:
                print(f"  ✅ Negative triggers: {neg_trigger_count} (target: 15+)")
            else:
                print(f"  ❌ Negative triggers: {neg_trigger_count} (target: 15+)")
                self.results["errors"].append(f"{clone.name}: Insufficient negative triggers ({neg_trigger_count})")
                clone_passed = False
            
            # Test 5: Trigger Reactions (minimum 5)
            reaction_count = len(clone.trigger_reactions)
            if reaction_count >= 5:
                print(f"  ✅ Trigger reactions: {reaction_count} (target: 5+)")
            else:
                print(f"  ❌ Trigger reactions: {reaction_count} (target: 5+)")
                self.results["errors"].append(f"{clone.name}: Insufficient trigger reactions ({reaction_count})")
                clone_passed = False
            
            # Test 6: System Prompt Quality (minimum 350 lines)
            try:
                system_prompt = clone.get_system_prompt()
                line_count = len(system_prompt.split('\n'))
                
                if line_count >= 350:
                    print(f"  ✅ System prompt: {line_count} lines (target: 350+)")
                else:
                    print(f"  ⚠️  System prompt: {line_count} lines (target: 350+)")
                    # Warning only, not a failure
            except Exception as e:
                print(f"  ❌ System prompt generation failed: {str(e)}")
                self.results["errors"].append(f"{clone.name}: System prompt error - {str(e)}")
                clone_passed = False
            
            # Test 7: Validation Method
            is_valid, validation_errors = clone.validate()
            if is_valid:
                print(f"  ✅ Validation: Passed")
            else:
                print(f"  ❌ Validation: Failed")
                for err in validation_errors:
                    print(f"      - {err}")
                    self.results["errors"].append(f"{clone.name}: {err}")
                clone_passed = False
            
            # Update results
            if clone_passed:
                self.results["passed"] += 1
                print(f"  🎉 {clone.name}: ALL TESTS PASSED")
            else:
                self.results["failed"] += 1
                print(f"  ⚠️  {clone.name}: SOME TESTS FAILED")
        
        return self.results
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Clones: {self.results['total_clones']}")
        print(f"Passed: {self.results['passed']} ✅")
        print(f"Failed: {self.results['failed']} ❌")
        
        if self.results["errors"]:
            print("\n❌ ERRORS:")
            for error in self.results["errors"]:
                print(f"  - {error}")
        
        print("\n" + "=" * 70)
        
        if self.results["failed"] == 0:
            print("🎉 ALL CLONES PASSED BEHAVIORAL TESTS!")
            print("=" * 70)
            return True
        else:
            print("⚠️  SOME CLONES NEED ATTENTION")
            print("=" * 70)
            return False


def main():
    """Run behavioral tests."""
    tester = CloneBehavioralTester()
    results = tester.run_all_tests()
    success = tester.print_summary()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
