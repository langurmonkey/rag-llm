#!python
from langchain_ollama import OllamaEmbeddings, OllamaLLM
import chromadb, requests, os, ollama

OLLAMA_URL = "http://localhost:11434"

models = ollama.list()
model_names = []
for m in models.models:
    model_names.append(m.model)

print("Available models:\n -", '\n - '.join(model_names))

# Ask the user the LLM model to use
llm_model = input("\nModel to use: ")

# Configure ChromaDB
# Initialize the ChromaDB client with persistent storage in the current directory
chroma_client = chromadb.PersistentClient(path=os.path.join(os.getcwd(), "chroma_db"))

# Define a custom embedding function for ChromaDB using Ollama
class ChromaDBEmbeddingFunction:
    """
    Custom embedding function for ChromaDB using embeddings from Ollama.
    """
    def __init__(self, langchain_embeddings):
        self.langchain_embeddings = langchain_embeddings

    def __call__(self, input):
        # Ensure the input is in a list format for processing
        if isinstance(input, str):
            input = [input]
        return self.langchain_embeddings.embed_documents(input)

# Initialize the embedding function with Ollama embeddings
embedding = ChromaDBEmbeddingFunction(
    OllamaEmbeddings(
        model=llm_model,
        base_url=OLLAMA_URL
    )
)

# Define a collection for the RAG workflow
collection_name = "rag_collection_demo"
collection = chroma_client.get_or_create_collection(
    name=collection_name,
    metadata={"description": "A collection for RAG with Ollama"},
    embedding_function=embedding  # Use the custom embedding function
)

# Function to add documents to the ChromaDB collection
def add_documents_to_collection(documents, ids):
    """
    Add documents to the ChromaDB collection.
    
    Args:
        documents (list of str): The documents to add.
        ids (list of str): Unique IDs for the documents.
    """
    collection.add(
        documents=documents,
        ids=ids
    )

# Example: Add sample documents to the collection
documents = [
    "The Mittius is a sphere of radius 2 that is used to disperse light in all directions. The Mittius is very powerful and sometimes emits light in various wavelengths on its own. It is a completely fictional object whose only purpose is testing RAG in a local LLM.",
    "The newly accessible mid-infrared (MIR) window offered by the James Webb Space Telescope (JWST) for exoplanet imaging is expected to provide valuable information to characterize their atmospheres. In particular, coronagraphs on board the JWST Mid-InfraRed instrument (MIRI) are capable of imaging the coldest directly imaged giant planets at the wavelengths where they emit most of their flux. The MIRI coronagraphs have been specially designed to detect the NH3 absorption around 10.5 microns, which has been predicted by atmospheric models. We aim to assess the presence of NH3 while refining the atmospheric parameters of one of the coldest companions detected by directly imaging GJ 504 b. Its mass is still a matter of debate and depending on the host star age estimate, the companion could either be placed in the brown dwarf regime or in the young Jovian planet regime. We present an analysis of MIRI coronagraphic observations of the GJ 504 system. We took advantage of previous observations of reference stars to build a library of images and to perform a more efficient subtraction of the stellar diffraction pattern. We detected the presence of NH3 at 12.5 sigma in the atmosphere, in line with atmospheric model expectations for a planetary-mass object and observed in brown dwarfs within a similar temperature range. The best-fit model with Exo-REM provides updated values of its atmospheric parameters, yielding a temperature of Teff = 512 K and radius of R = 1.08 RJup. These observations demonstrate the capability of MIRI coronagraphs to detect NH3 and to provide the first MIR observations of one of the coldest directly imaged companions. Overall, NH3 is a key molecule for characterizing the atmospheres of cold planets, offering valuable insights into their surface gravity. These observations provide valuable information for spectroscopic observations planned with JWST.",
    "Gaia Sky has a new website built with Hugo. It contains download pages for all new and old versions of the software, and a full listing of all the catalogs and datasets offered with the software. The datasets can be downloaded in-app with the provided dataset manager."

]
doc_ids = ["doc_mittius", "doc_paper_jwst", "doc_gaiasky_web"]

# Documents only need to be added once or whenever an update is required. 
# This line of code is included for demonstration purposes:
add_documents_to_collection(documents, doc_ids)

# Function to query the ChromaDB collection
def query_chromadb(query_text, n_results=3):
    """
    Query the ChromaDB collection for relevant documents.
    
    Args:
        query_text (str): The input query.
        n_results (int): The number of top results to return.
    
    Returns:
        list of dict: The top matching documents and their metadata.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results
    )
    return results["documents"], results["metadatas"]

# Function to interact with the Ollama LLM
def query_ollama(prompt):
    """
    Send a query to Ollama and retrieve the response.
    
    Args:
        prompt (str): The input prompt for Ollama.
    
    Returns:
        str: The response from Ollama.
    """
    llm = OllamaLLM(model=llm_model)
    return llm.invoke(prompt)

# RAG pipeline: Combine ChromaDB and Ollama for Retrieval-Augmented Generation
def rag_pipeline(query_text):
    """
    Perform Retrieval-Augmented Generation (RAG) by combining ChromaDB and Ollama.
    
    Args:
        query_text (str): The input query.
    
    Returns:
        str: The generated response from Ollama augmented with retrieved context.
    """
    # Step 1: Retrieve relevant documents from ChromaDB
    retrieved_docs, metadata = query_chromadb(query_text)
    context = " ".join(retrieved_docs[0]) if retrieved_docs else "No relevant documents found."

    # Step 2: Send the query along with the context to Ollama
    augmented_prompt = f"Context: {context}\nQuestion: {query_text}\nAnswer: "
    # Uncomment next line if you want to see the context
    # print(augmented_prompt)

    response = query_ollama(augmented_prompt)
    return response

# User query loop
while True:
    query = input("Ask a question (or type 'exit' to quit): ")
    if query.lower() == "exit":
        break
    response = rag_pipeline(query)
    print(response)

