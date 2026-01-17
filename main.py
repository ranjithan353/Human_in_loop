"""
Main Script - Human-in-the-Loop Social Media Manager
====================================================
This script starts the workflow by reading a news article and generating a post.
The workflow will interrupt and wait for human approval.
"""

from workflow import SocialMediaWorkflow
from langgraph.checkpoint.sqlite import SqliteSaver
import sys
import uuid
from datetime import datetime
import io
import os
import sqlite3

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


def read_article_from_file(file_path: str) -> str:
    """
    Read article text from a file.
    
    Args:
        file_path: Path to the text file containing the article
        
    Returns:
        Article text as string
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        print(f"❌ Error: File '{file_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        sys.exit(1)


def read_article_from_input() -> str:
    """
    Read article text from user input (stdin).
    
    Returns:
        Article text as string
    """
    print("Enter the news article text (press Ctrl+D or Ctrl+Z when finished):")
    print("-" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        # User pressed Ctrl+D (Unix) or Ctrl+Z (Windows)
        pass
    
    article = "\n".join(lines).strip()
    
    if not article:
        print("❌ Error: No article text provided.")
        sys.exit(1)
    
    return article


def main():
    """
    Main function to start the social media post generation workflow.
    """
    print("=" * 60)
    print("🚀 Human-in-the-Loop Social Media Manager")
    print("=" * 60)
    print()
    
    # Initialize workflow with SqliteSaver for persistent state storage
    # SqliteSaver persists state to disk, allowing the workflow to resume after restart
    # Both main.py and approve_post.py use the same database file to share state
    db_path = os.path.join(os.path.dirname(__file__), ".checkpoints.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)
    workflow = SocialMediaWorkflow(checkpointer=checkpointer)
    
    # Get article input
    if len(sys.argv) > 1:
        # Article provided as file path
        article_path = sys.argv[1]
        print(f"📄 Reading article from: {article_path}")
        article = read_article_from_file(article_path)
    else:
        # Read article from stdin
        article = read_article_from_input()
    
    # Generate unique thread_id for this workflow run
    # This allows multiple workflows to run in parallel
    thread_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    print(f"\n📝 Article loaded ({len(article)} characters)")
    print(f"🆔 Thread ID: {thread_id}")
    print()
    
    try:
        # Run the workflow
        # The workflow will interrupt at the "wait_for_approval" node
        print("▶️  Starting workflow...")
        print()
        
        # Use interrupt_before to pause before the wait_for_approval node
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Initial state
        initial_state = {
            "article": article,
            "generated_post": "",
            "human_feedback": "",
            "is_approved": False,
            "is_published": False,
            "iteration_count": 0
        }
        
        # Run until interrupt
        # We'll interrupt before "wait_for_approval" to pause for human review
        # LangGraph will automatically pause at the interrupt point
        config_with_interrupt = {
            "configurable": {
                "thread_id": thread_id,
                "interrupt_before": ["wait_for_approval"]
            }
        }
        
        # Stream the workflow execution
        # This will stop at the interrupt point (wait_for_approval node)
        # The interrupt_before config will cause the workflow to pause
        for event in workflow.graph.stream(initial_state, config=config_with_interrupt):
            # Check state after each event to see if we're at an interrupt
            current_state = workflow.graph.get_state(config_with_interrupt)
            if current_state and hasattr(current_state, 'next') and current_state.next:
                # Check if next node is wait_for_approval (meaning we're paused before it)
                if any("wait_for_approval" in str(node) for node in current_state.next):
                    # We've hit the interrupt point, break the loop
                    break
            # Also check event names
            for node_name in event.keys():
                if node_name == "wait_for_approval":
                    # We've reached wait_for_approval, check if we should stop
                    break
        
        print("\n" + "=" * 60)
        print("✅ Workflow paused. Use approve_post.py to continue.")
        print(f"   Thread ID: {thread_id}")
        print("=" * 60)
        
        # Save thread_id to a file so approve_post.py can use it
        with open("current_thread_id.txt", "w") as f:
            f.write(thread_id)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
#this file as be modified by team 

if __name__ == "__main__":
    main()

