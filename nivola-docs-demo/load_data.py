import argparse
import chromadb
from json import load

def loadJsonFile(file: str) -> dict:
    with open(file,'r', encoding='utf-8') as f:
        if(f.readable()):
            return load(f)
        else: 
            print(f'Error while reading {file}')
            exit()

def main(collection_name: str = "nivola-wiki", persist_directory: str = ".", reset: bool = False):
    filename = 'db.json' 
    doc = [] 
    metadata = []
    ids = []

    for obj in loadJsonFile(filename): 
        doc.append(f'<DOC> <TITLE>{obj["title"]}</TITLE> <KEYWORDS>{", ".join(obj["keywords"])}</KEYWORDS> <TEXT>{obj["text"]}</TEXT> </DOC>')
        ids.append(obj['hash'])
        metadata.append({
            'link': obj['link'],
            'category': obj['category'],
            # 'list': '\n-'.join(obj['list']),
            # 'table': str(obj['table'])
        })

    if len(doc)!=len(metadata):
        print('Error while loading db.json')
        exit(1)

    # Instantiate a persistent chroma client in the persist_directory.
    # Learn more at docs.trychroma.com
    client = chromadb.PersistentClient(path=persist_directory)
    if reset:
        client.reset()

    # If the collection already exists, we just return it. This allows us to add more
    # data to an existing collection.
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"} # l2 is the default
    )

    # print(type(doc_embeddings[0]), doc_embeddings)

    count = collection.count()
    print(f"Collection already contains {count} documents")

    for index, id in enumerate(ids):
        collection.add(
            ids=id,
            documents=doc[index],
            metadatas=metadata[index]
        )

    new_count = collection.count()
    print(f"Added {new_count - count} documents")

if __name__ == "__main__":
    # Read the data directory, collection name, and persist directory
    parser = argparse.ArgumentParser(
        description="Load documents from a directory into a Chroma collection"
    )

    # Add arguments
    parser.add_argument(
        "--collection_name",
        type=str,
        default="nivola-wiki",
        help="The name of the Chroma collection",
    )
    parser.add_argument(
        "--persist_directory",
        type=str,
        default="chroma_storage",
        help="The directory where you want to store the Chroma collection",
    )

    # Parse arguments
    args = parser.parse_args()

    main(
        collection_name=args.collection_name,
        persist_directory=args.persist_directory
    )