"""
LangGraph Workflow Module
=========================
This module defines the LangGraph workflow with interrupts and checkpoints.
The workflow generates a post and then pauses for human approval.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from post_generator import PostGenerator


# Define the state structure for our workflow
class WorkflowState(TypedDict):
    """
    State structure that persists throughout the workflow.
    
    Fields:
        article: The original news article text
        generated_post: The AI-generated social media post
        human_feedback: Feedback from human (approve/edit instructions)
        is_approved: Whether the post has been approved
        is_published: Whether the post has been published to Twitter
        iteration_count: Number of regeneration attempts
    """
    article: str
    generated_post: str
    human_feedback: str
    is_approved: bool
    is_published: bool
    iteration_count: int


class SocialMediaWorkflow:
    """
    LangGraph workflow for human-in-the-loop social media post generation.
    """
    
    def __init__(self, checkpointer=None):
        """
        Initialize the workflow with an optional checkpointer.
        
        Args:
            checkpointer: A checkpointer instance (e.g., MemorySaver) for state persistence
        """
        # Initialize the post generator
        self.post_generator = PostGenerator()
        
        # Create checkpointer if not provided (uses MemorySaver by default)
        # MemorySaver persists state in memory, allowing workflow to resume after restart
        if checkpointer is None:
            self.checkpointer = MemorySaver()
        else:
            self.checkpointer = checkpointer
        
        # Build the workflow graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow with nodes and edges.
        
        Returns:
            A compiled StateGraph ready for execution
        """
        # Create a new StateGraph with our WorkflowState
        workflow = StateGraph(WorkflowState)
        
        # Add nodes to the graph
        # Each node is a function that processes the state
        
        # Node 1: Generate post from article
        workflow.add_node("generate_post", self._generate_post_node)
        
        # Node 2: Wait for human approval (this is where we interrupt)
        workflow.add_node("wait_for_approval", self._wait_for_approval_node)
        
        # Node 3: Process human feedback (approve or edit)
        workflow.add_node("process_feedback", self._process_feedback_node)
        
        # Node 4: Publish to Twitter (if approved)
        workflow.add_node("publish_post", self._publish_post_node)
        
        # Define the workflow edges (how nodes connect)
        
        # Start: Generate post from article
        workflow.set_entry_point("generate_post")
        
        # After generating, wait for approval (with interrupt)
        workflow.add_edge("generate_post", "wait_for_approval")
        
        # After waiting, process the feedback
        workflow.add_edge("wait_for_approval", "process_feedback")
        
        # After processing feedback, check if approved
        workflow.add_conditional_edges(
            "process_feedback",
            self._should_publish,  # Decision function
            {
                "publish": "publish_post",  # If approved, publish
                "regenerate": "generate_post",  # If needs editing, regenerate
                "end": END  # If max iterations reached, end
            }
        )
        
        # After publishing, end the workflow
        workflow.add_edge("publish_post", END)
        
        # Compile the graph with checkpointer for state persistence
        return workflow.compile(checkpointer=self.checkpointer)
    
    def _generate_post_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node that generates a social media post from the article.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with generated_post field
        """
        print("\n🤖 Generating post from article...")
        
        # Check if we need to regenerate based on feedback
        if state.get("human_feedback") and state.get("iteration_count", 0) > 0:
            # Regenerate based on feedback
            print(f"📝 Regenerating post based on feedback: {state['human_feedback']}")
            post = self.post_generator.regenerate_post(
                state["article"],
                state["human_feedback"]
            )
        else:
            # Generate new post from article
            post = self.post_generator.generate_post(state["article"])
        
        # Update state with generated post
        state["generated_post"] = post
        state["iteration_count"] = state.get("iteration_count", 0) + 1
        
        print(f"✓ Post generated ({state['iteration_count']} attempt):")
        print(f"\n{'-' * 60}")
        print(post)
        print(f"{'-' * 60}\n")
        
        return state
    
    def _wait_for_approval_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node that waits for human approval.
        This node uses LangGraph's interrupt feature to pause execution.
        
        Args:
            state: Current workflow state
            
        Returns:
            State (unchanged, waiting for human input)
        """
        print("\n⏸️  Workflow paused - Waiting for human approval...")
        print("💡 Use the approval script to review and approve/edit the post.")
        print("   Run: python approve_post.py")
        
        # This node doesn't modify state
        # The interrupt happens automatically when this node is reached
        # The workflow will pause here until resumed with human feedback
        
        return state
    
    def _process_feedback_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node that processes human feedback (approve or edit instructions).
        
        Args:
            state: Current workflow state with human_feedback
            
        Returns:
            Updated state with is_approved flag
        """
        feedback = state.get("human_feedback", "").lower().strip()
        
        # Check if feedback indicates approval
        if feedback in ["approve", "yes", "ok", "publish", "y"]:
            state["is_approved"] = True
            print("\n✓ Post approved by human!")
        else:
            # Feedback contains editing instructions
            state["is_approved"] = False
            print(f"\n📝 Post needs editing. Feedback: {state['human_feedback']}")
        
        return state
    
    def _publish_post_node(self, state: WorkflowState) -> WorkflowState:
        """
        Node that publishes the post to Twitter.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with is_published flag
        """
        from twitter_client import TwitterClient
        
        print("\n📤 Publishing post to Twitter...")
        
        try:
            # Initialize Twitter client
            twitter = TwitterClient()
            
            # Publish the post
            result = twitter.publish_post(state["generated_post"])
            
            if result["success"]:
                state["is_published"] = True
                print(f"\n✅ {result['message']}")
            else:
                print(f"\n❌ Error: {result['error']}")
                state["is_published"] = False
                
        except Exception as e:
            print(f"\n❌ Failed to publish: {str(e)}")
            state["is_published"] = False
        
        return state
    
    def _should_publish(self, state: WorkflowState) -> str:
        """
        Conditional function to decide next step after processing feedback.
        
        Args:
            state: Current workflow state
            
        Returns:
            "publish" if approved, "regenerate" if needs editing, "end" if max iterations
        """
        # Check if approved
        if state.get("is_approved", False):
            return "publish"
        
        # Check if we've exceeded max regeneration attempts (prevent infinite loops)
        max_iterations = 5
        if state.get("iteration_count", 0) >= max_iterations:
            print(f"\n⚠️  Maximum regeneration attempts ({max_iterations}) reached.")
            return "end"
        
        # Needs regeneration
        return "regenerate"
    
    def run(self, article: str, thread_id: str = "default") -> dict:
        """
        Run the workflow with a news article.
        
        Args:
            article: The news article text
            thread_id: Unique identifier for this workflow run (for checkpointing)
            
        Returns:
            Configuration for running the workflow
        """
        # Initial state
        initial_state = {
            "article": article,
            "generated_post": "",
            "human_feedback": "",
            "is_approved": False,
            "is_published": False,
            "iteration_count": 0
        }
        
        # Create the workflow configuration with thread_id for checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Run the workflow
        # The workflow will interrupt at "wait_for_approval" node
        # Use interrupt_before=["wait_for_approval"] to pause before that node
        result = self.graph.invoke(
            initial_state,
            config=config
        )
        
        return result
    
    def resume(self, human_feedback: str, thread_id: str = "default") -> dict:
        """
        Resume the workflow after human provides feedback.
        
        Args:
            human_feedback: "approve" or editing instructions
            thread_id: The same thread_id used in the initial run
            
        Returns:
            Final workflow state
        """
        # Get the current state from checkpoint
        config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        
        # Update state with human feedback
        # We need to update the state and then continue execution
        current_state = self.graph.get_state(config)
        
        if current_state is None or current_state.values == {}:
            raise ValueError(f"No workflow state found for thread_id: {thread_id}")
        
        # Update the state with feedback
        updated_state = current_state.values.copy()
        updated_state["human_feedback"] = human_feedback
        
        # Continue execution from where it was interrupted
        # The workflow will continue from "wait_for_approval" node
        result = self.graph.invoke(
            updated_state,
            config=config
        )
        
        return result

