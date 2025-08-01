```python
import os
from typing import List, Dict, Tuple, Optional
import nltk
from langchain.tools import DuckDuckGoSearchResults
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from dotenv import load_dotenv

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

# Load environment variables
load_dotenv()

# Set OpenAI API key
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY') or ''

# Initialize DuckDuckGo Search
search = DuckDuckGoSearchResults()

class SummarizeText(BaseModel):
    """Model for text to be summarized."""
    text: str = Field(..., title="Text to summarize", description="The text to be summarized")

    @staticmethod
    def parse_search_results(results_string: str) -> List[Dict[str, str]]:
        """Parse a string representation of search results into a list of dictionaries."""
        try:
            results = []
            entries = results_string.split(', snippet: ')
            for entry in entries[1:]:  # Skip the first split as it's empty
                parts = entry.split(', title: ')
                if len(parts) == 2:
                    snippet = parts[0].strip()
                    title_link = parts[1].split(', link: ')
                    if len(title_link) == 2:
                        title, link = title_link
                        results.append({
                            'snippet': snippet,
                            'title': title.strip(),
                            'link': link.strip()
                        })
            return results
        except Exception as e:
            print(f"Error parsing search results: {str(e)}")
            return []

    @staticmethod
    def perform_web_search(query: str, specific_site: Optional[str] = None) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Perform a web search based on a query, optionally including a specific website."""
        try:
            if specific_site:
                specific_query = f"site:{specific_site} {query}"
                print(f"Searching for: {specific_query}")
                specific_results = search.run(specific_query)
                print(f"Specific search results: {specific_results}")
                specific_parsed = SummarizeText.parse_search_results(specific_results)
                
                general_query = f"-site:{specific_site} {query}"
                print(f"Searching for: {general_query}")
                general_results = search.run(general_query)
                print(f"General search results: {general_results}")
                general_parsed = SummarizeText.parse_search_results(general_results)
                
                combined_results = (specific_parsed + general_parsed)[:3]
            else:
                print(f"Searching for: {query}")
                web_results = search.run(query)
                print(f"Web results: {web_results}")
                combined_results = SummarizeText.parse_search_results(web_results)[:3]
            
            web_knowledge = [result.get('snippet', '') for result in combined_results]
            sources = [(result.get('title', 'Untitled'), result.get('link', '')) for result in combined_results]
            
            print(f"Processed web_knowledge: {web_knowledge}")
            print(f"Processed sources: {sources}")
            return web_knowledge, sources
        except Exception as e:
            print(f"Error in perform_web_search: {str(e)}")
            return [], []

    @staticmethod
    def summarize_text(text: str, source: Tuple[str, str]) -> str:
        """Summarize the given text using OpenAI's language model."""
        try:
            llm = ChatOpenAI(temperature=0.7, model="gpt-4o-mini")
            prompt_template = PromptTemplate(
                template="Please summarize the following text in 1-2 bullet points:\n\n{text}\n\nSummary:",
                input_variables=["text"]
            )
            summary_chain = prompt_template | llm
            input_data = {"text": text}
            summary = summary_chain.invoke(input_data)
            
            summary_content = summary.content if hasattr(summary, 'content') else str(summary)
            formatted_summary = f"Source: {source[0]} ({source[1]})\n{summary_content.strip()}\n"
            return formatted_summary
        except Exception as e:
            print(f"Error in summarize_text: {str(e)}")
            return ""

    @staticmethod
    def search_summarize(query: str, specific_site: Optional[str] = None) -> str:
        """Perform a web search and summarize the results."""
        web_knowledge, sources = SummarizeText.perform_web_search(query, specific_site)
        
        if not web_knowledge or not sources:
            print("No web knowledge or sources found.")
            return ""
        
        summaries = [
            SummarizeText.summarize_text(knowledge, source)
            for knowledge, source in zip(web_knowledge, sources)
            if knowledge.strip()
        ]
        
        return "\n".join(summaries)

# Example usage
if __name__ == "__main__":
    query = "What are the latest advancements in artificial intelligence?"
    specific_site = None
    result = SummarizeText.search_summarize(query, specific_site)
    print(f"Summary of latest advancements in AI (including information from {specific_site if specific_site else 'various sources'}):")
    print(result)
```