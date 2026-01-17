"""
Approval Script - Human-in-the-Loop Social Media Manager
=========================================================
This script allows humans to review, approve, or edit generated posts.
It resumes the workflow after human feedback.
"""

from workflow import SocialMediaWorkflow
from langgraph.checkpoint.sqlite import SqliteSaver
import sys
import os
import io
import sqlite3

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def get_current_thread_id() -> str:
    """
    Get the thread_id from the saved file or prompt user.
    
    Returns:
        Thread ID string
    """
    # Try to read from file first
    if os.path.exists("current_thread_id.txt"):
        with open("current_thread_id.txt", "r") as f:
            thread_id = f.read().strip()
            if thread_id:
                return thread_id
    
    # If no file, prompt user
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        print("Enter the thread ID (or leave empty to use default):")
        thread_id = input().strip()
        return thread_id if thread_id else "default"


def display_post(state: dict):
    """
    Display the generated post in a user-friendly format.
    
    Args:
        state: Current workflow state
    """
    print("\n" + "=" * 60)
    print("📋 GENERATED POST")
    print("=" * 60)
    print()
    print(state.get("generated_post", "No post generated yet."))
    print()
    print("=" * 60)
    print(f"Character count: {len(state.get('generated_post', ''))}")
    print(f"Regeneration attempts: {state.get('iteration_count', 0)}")
    print("=" * 60)
    print()


def get_human_feedback() -> str:
    """
    Get feedback from human (approve or edit instructions).
    
    Returns:
        "approve" or editing instructions
    """
    print("\n" + "=" * 60)
    print("👤 HUMAN REVIEW")
    print("=" * 60)
    print()
    print("Options:")
    print("  1. Type 'approve' (or 'yes', 'ok', 'publish') to publish the post")
    print("  2. Type editing instructions to regenerate the post")
    print("  3. Type 'quit' to exit without publishing")
    print()
    print("Examples of editing instructions:")
    print("  - 'Make it more casual'")
    print("  - 'Add more emojis'")
    print("  - 'Focus on the main benefit'")
    print("  - 'Make it shorter'")
    print("  - 'Change tone to friendly'")
    print()
    
    feedback = input("Your feedback: ").strip()
    
    if feedback.lower() in ["quit", "exit", "q"]:
        print("\n👋 Exiting without publishing.")
        sys.exit(0)
    
    return feedback


def main():
    """
    Main function for human approval workflow.
    """
    print("=" * 60)
    print("👤 Human Approval Interface")
    print("=" * 60)
    
    # Get thread ID
    thread_id = get_current_thread_id()
    print(f"\n🆔 Thread ID: {thread_id}")
    
    # Initialize workflow with same checkpointer (same database file as main.py)
    # This allows approve_post.py to access state saved by main.py
    db_path = os.path.join(os.path.dirname(__file__), ".checkpoints.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    workflow = SocialMediaWorkflow(checkpointer=checkpointer)
    
    # Get current state
    config = {
        "configurable": {
            "thread_id": thread_id
        }
    }
    
    try:
        # Get the current state from checkpoint
        current_state = workflow.graph.get_state(config)
        
        if current_state is None or not current_state.values:
            print(f"\n❌ Error: No workflow state found for thread_id: {thread_id}")
            print("   Make sure you've run main.py first to generate a post.")
            sys.exit(1)
        
        # Display the generated post
        display_post(current_state.values)
        
        # Get human feedback
        feedback = get_human_feedback()
        
        if not feedback:
            print("\n⚠️  No feedback provided. Exiting.")
            sys.exit(0)
        
        # Resume workflow with feedback
        print("\n▶️  Resuming workflow with your feedback...")
        print()
        
        # Update state with feedback
        updated_state = current_state.values.copy()
        updated_state["human_feedback"] = feedback
        
        # Update the checkpoint state
        workflow.graph.update_state(config, updated_state)
        
        # Continue execution from where it was interrupted
        # Remove interrupt to continue execution
        continue_config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Stream the rest of the workflow
        for event in workflow.graph.stream(None, config=continue_config):
            # Process events as they come
            pass
        
        # Check final state
        final_state = workflow.graph.get_state(config)
        
        if final_state.values.get("is_published", False):
            print("\n" + "=" * 60)
            print("✅ Workflow completed successfully!")
            print("=" * 60)
        elif final_state.values.get("is_approved", False):
            print("\n" + "=" * 60)
            print("✅ Post approved but not published (check Twitter client)")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("📝 Post regenerated. Run this script again to review.")
            print("=" * 60)
            print(f"\n💡 Thread ID: {thread_id}")
            print("   Run: python approve_post.py {thread_id}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

