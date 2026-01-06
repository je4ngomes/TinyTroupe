"""
Various utility functions for behavior analysis and action similarity computation.
"""

import textdistance



def next_action_jaccard_similarity(agent, proposed_next_action):
    """
    Computes the Jaccard similarity between the agent's current action and a proposed next action,
    modulo target and type (i.e., similarity will be computed using only the content, provided that the action 
    type and target are the same). If the action type or target is different, the similarity will be 0.

    Jaccard similarity is a measure of similarity between two sets, defined as the size of the intersection 
    divided by the size of the union of the sets.

    Args:
        agent (TinyPerson): The agent whose current action is to be compared.
        proposed_next_action (dict): The proposed next action to be compared against the agent's current action.

    Returns:
        float: The Jaccard similarity score between the agent's current action and the proposed next action.
    """
    # Get the agent's current action
    current_action = agent.last_remembered_action()
    
    if current_action is None:
        return 0.0
    
    # Check if the action type and target are the same
    if ("type" in current_action) and ("type" in proposed_next_action) and ("target" in current_action) and ("target" in proposed_next_action) and \
            (current_action["type"] != proposed_next_action["type"] or current_action["target"] != proposed_next_action["target"]):
        return 0.0
    
    # Compute the Jaccard similarity between the content of the two actions
    current_action_content = current_action["content"]
    proposed_next_action_content = proposed_next_action["content"]

    # using textdistance to compute the Jaccard similarity
    jaccard_similarity = textdistance.jaccard(current_action_content, proposed_next_action_content)

    return jaccard_similarity


def has_stimulus_since_last_action(agent):
    """
    Check if there has been a stimulus since the last substantive action.

    This helps distinguish between:
    - Agent looping (no new stimulus) - should be prevented
    - Agent responding to repeated inputs (new stimulus) - should be allowed

    Args:
        agent (TinyPerson): The agent to check

    Returns:
        bool: True if there's been a stimulus since last action, False otherwise
    """
    # Get recent memory items (both actions and stimuli)
    memory_items = agent.episodic_memory.retrieve_last(n=10, include_omission_info=False)

    if not memory_items:
        return False

    # Walk backwards through memory
    # If we encounter a stimulus before an action, return True
    # If we encounter an action before a stimulus, return False
    for item in reversed(memory_items):
        item_type = item.get('type')

        if item_type == 'stimulus':
            return True  # Found stimulus before action
        elif item_type == 'action':
            action_content = item.get('content', {}).get('action', {})
            # Ignore DONE actions as they're not substantive
            if action_content.get('type') != 'DONE':
                return False  # Found substantive action before stimulus

    # If we didn't find either, assume no stimulus
    return False