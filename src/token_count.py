import tiktoken

def message_token_count(message, num_tokens):
        encoding = tiktoken.get_encoding("cl100k_base")

        for key, value in message.items():
                num_tokens += len(encoding.encode(value))

                if key == "name": num_tokens -= 1
                
        return num_tokens
    
def num_tokens_from_messages(messages):
        """Returns the number of tokens used by a list of messages."""

        num_tokens = 0

        for message in messages:
                num_tokens += 4  # every message follows <im_start>{role/name}\n{content}<im_end>\n        
                num_tokens = message_token_count(message, num_tokens)
        
        num_tokens += 2  # every reply is primed with <im_start>assistant
        return num_tokens

def ensure_fit_tokens(messages, max_tokens:int = int(1.25e+5)):
    """
    Ensure that total tokens in messages is less than MAX_TOKENS.
    If not, remove oldest messages until it fits.
    """
    total_tokens = num_tokens_from_messages(messages)

    while total_tokens > max_tokens:
        messages.pop(0)
        total_tokens = num_tokens_from_messages(messages)