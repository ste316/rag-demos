import argparse
from typing import List, Dict
from openai.types.chat import ChatCompletionMessageParam
import openai
import chromadb
from re import sub
from dotenv import dotenv_values
from os import getcwd
from os.path import join

def build_prompt(query: str, context: List[str]) -> List[ChatCompletionMessageParam]:
    """
    Builds a prompt for the LLM. #

    This function builds a prompt for the LLM. It takes the original query,
    and the returned context, and asks the model to answer the question based only
    on what's in the context, not what's in its weights.

    More information: https://platform.openai.com/docs/guides/chat/introduction

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A prompt for the LLM (List[ChatCompletionMessageParam]).
    """
    temp = open(join(getcwd(), 'prompts', 'claude.md'), 'r', encoding='utf-8').read()
    # temp = sub(r'\s+', ' ', temp)
    system: ChatCompletionMessageParam = {
        "role": "system",
        'content': temp
    }
    
    user: ChatCompletionMessageParam = {
        "role": "user",
        "content": f"Documents: {(" ").join(context)}\nQuestion: {query}",
    } 

    return [system, user]

def get_chatGPT_response(query: str, context: List[str], model_name: str) -> str:
    """
    Queries the GPT API to get a response to the question.

    Args:
    query (str): The original query.
    context (List[str]): The context of the query, returned by embedding search.

    Returns:
    A response to the question.
    """
    msg = build_prompt(query, context)
    print(msg)
    response = openai.chat.completions.create(
        model=model_name,
        messages=msg,
    )

    return response.choices[0].message.content  # type: ignore

def load_env_file(file_path: str = '.env') -> dict:
    """
    Load variables from a .env file into a dictionary.

    Args:
        file_path (str): Path to the .env file. Default is '.env'.

    Returns:
        dict: A dictionary containing the key-value pairs from the .env file.
    """
    return dotenv_values(file_path)

def main(collection_name: str = "nivola-wiki", persist_directory: str = ".") -> None:
    # Check if the OPENAI_API_KEY environment variable is set. Prompt the user to set it if not.
    # if "OPENAI_API_KEY" not in os.environ: openai.api_key = input("Please enter your OpenAI API Key. You can get it from https://platform.openai.com/account/api-keys\n")
    env = load_env_file()

    openai.api_key = env['OPENAI_KEY']

    # Ask what model to use
    model_name = "gpt-3.5-turbo"
    answer = input(f"Do you want to use GPT-4? (y/n) (default is {model_name}): ")
    if answer == "y":
        model_name = "gpt-4"

    # Instantiate a persistent chroma client in the persist_directory.
    # This will automatically load any previously saved collections.
    # Learn more at docs.trychroma.com
    client = chromadb.PersistentClient(path=persist_directory)

    # Get the collection.
    collection = client.get_collection(name=collection_name)

    # We use a simple input loop.
    while True:
        # Get the user's 
        try:
            query = input("Query: ")
        except KeyboardInterrupt:
            exit(0)
        if len(query) == 0:
            print("Please enter a question. Ctrl+C to Quit.\n")
            continue
        print(f"\nThinking using {model_name}...\n")

        # Query the collection to get the 5 most relevant results
        results = collection.query(
            query_texts=[query], n_results=5, include=["documents", "metadatas"]
        )

        sources = "\n".join(
            [
                f"{result['link']}: category {result['category']}"
                for result in results["metadatas"][0] 
            ]
        )

        # Get the response from GPT
        response = get_chatGPT_response(query, results["documents"][0], model_name) 

        # Output, with sources
        print('\n\nRESPONSE:\n'+response)
        print("\n")
        print(f"Source documents:\n{sources}")
        print("\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Load documents from a directory into a Chroma collection"
    )

    parser.add_argument(
        "--persist_directory",
        type=str,
        default="chroma_storage",
        help="The directory where you want to store the Chroma collection",
    )
    parser.add_argument(
        "--collection_name",
        type=str,
        default="nivola-wiki",
        help="The name of the Chroma collection",
    )

    # Parse arguments
    args = parser.parse_args()

    main(
        collection_name=args.collection_name,
        persist_directory=args.persist_directory,
    )