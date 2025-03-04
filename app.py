import json
from gnews import GNews
import newspaper
import google.generativeai as genai
from collections import defaultdict
from googlenewsdecoder import gnewsdecoder

# Initialize Gemini API
GEMINI_API_KEY = "AIzaSyCsc_ClsvSjLymAZFwZIHITfiaNzA4lvh4"  # Replace with your Gemini API key
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Initialize GNews
google_news = GNews()
google_news = GNews(
    language='en',
    country='IN',
    period='7d',
    start_date=None,
    end_date=None,
    max_results=10,
)

# Dictionary to store user preferences
user_preferences = defaultdict(int)

# Mapping of user topics to valid GNews topic
VALID_TOPIC = [
    "WORLD", "NATION", "BUSINESS", "TECHNOLOGY", "ENTERTAINMENT", "SPORTS", "SCIENCE", "HEALTH", 
    "POLITICS", "CELEBRITIES", "TV", "MUSIC", "MOVIES", "THEATER", "SOCCER", "CYCLING", "MOTOR SPORTS", 
    "TENNIS", "COMBAT SPORTS", "BASKETBALL", "BASEBALL", "FOOTBALL", "SPORTS BETTING", "WATER SPORTS", 
    "HOCKEY", "GOLF", "CRICKET", "RUGBY", "ECONOMY", "PERSONAL FINANCE", "FINANCE", "DIGITAL CURRENCIES", 
    "MOBILE", "ENERGY", "GAMING", "INTERNET SECURITY", "GADGETS", "VIRTUAL REALITY", "ROBOTICS", 
    "NUTRITION", "PUBLIC HEALTH", "MENTAL HEALTH", "MEDICINE", "SPACE", "WILDLIFE", "ENVIRONMENT", 
    "NEUROSCIENCE", "PHYSICS", "GEOLOGY", "PALEONTOLOGY", "SOCIAL SCIENCES", "EDUCATION", "JOBS", 
    "ONLINE EDUCATION", "HIGHER EDUCATION", "VEHICLES", "ARTS-DESIGN", "BEAUTY", "FOOD", "TRAVEL", 
    "SHOPPING", "HOME", "OUTDOORS", "FASHION"
]


def get_news(topic, liked_factor):
    """
    Fetch news articles for a given topic and liked_factor.

    Args:
        topic (str): The topic to fetch news for.
        liked_factor (float): A value between 0 and 1 indicating the user's preference for the topic.

    Returns:
        list: A list of news articles (dictionaries) for the given topic.
    """
    try:
        # Fetch news articles for the topic using GNews
        articles = google_news.get_news_by_topic(topic)
        
        # Limit the number of articles based on liked_factor
        max_articles = int(10 * liked_factor)  # Adjust the multiplier as needed
        return articles[:max_articles]
    except Exception as e:
        print(f"Error fetching news for topic '{topic}': {e}")
        return []

def fetch_top_headlines():
    """Fetch top headlines using GNews."""
    headlines = google_news.get_top_news()
    return headlines if headlines else []

def display_headlines(headlines):
    """Display headlines in a readable format."""
    for idx, headline in enumerate(headlines):
        print(f"{idx + 1}. {headline['title']} - {headline['published date']}")

def resolve_final_url(url):
    interval_time = 1  # interval is optional, default is None

    decoded_url = gnewsdecoder(url, interval=interval_time)

    return decoded_url["decoded_url"]
    

def scrape_article(url):
    """Scrape article content using newspaper3k."""
    try:
        # Resolve the final URL
        final_url = resolve_final_url(url)
        print(f"Final URL: {final_url}")

        # Use newspaper3k to scrape the article
        article = newspaper.Article(final_url)
        article.download()
        article.parse()
        return article.text  # Use the .text attribute to get the article content
    except Exception as e:
        print(f"Error scraping article: {e}")
        return None

def summarize_with_gemini(text):
    """Summarize article content using Gemini."""
    if not text:
        return "Summary unavailable: Article text is empty or could not be scraped."
    
    try:
        response = model.generate_content(f"Summarize the following article in 3 sentences: {text}.")
        return response.text
    except Exception as e:
        print(f"Error summarizing with Gemini: {e}")
        return "Summary unavailable due to an error."

def get_topic(article_text):
    """
    Extract topics from the article using Gemini.

    Args:
        article_text (str): The text of the article.

    Returns:
        list: A list of topics (strings) extracted from the article.
    """
    if not article_text:
        return []  # Return an empty list if the article text is empty

    try:
        # Prompt Gemini to extract topics
        prompt = (
            "Categorize the following article into one or more of the follwing topics. Seperate the values by space and do not add anyother information. Only the topics [WORLD, NATION, BUSINESS, TECHNOLOGY, ENTERTAINMENT, SPORTS, SCIENCE, HEALTH, POLITICS, CELEBRITIES, TV, MUSIC, MOVIES, THEATER, SOCCER, CYCLING, MOTOR SPORTS, TENNIS, COMBAT SPORTS, BASKETBALL, BASEBALL, FOOTBALL, SPORTS BETTING, WATER SPORTS, HOCKEY, GOLF,  CRICKET, RUGBY, ECONOMY, PERSONAL FINANCE, FINANCE, DIGITAL CURRENCIES, MOBILE, ENERGY, GAMING, INTERNET SECURITY, GADGETS, VIRTUAL REALITY, ROBOTICS, NUTRITION, PUBLIC HEALTH, MENTAL HEALTH, MEDICINE, SPACE, WILDLIFE, ENVIRONMENT, NEUROSCIENCE, PHYSICS, GEOLOGY, PALEONTOLOGY, SOCIAL SCIENCES, EDUCATION, JOBS, ONLINE EDUCATION, HIGHER EDUCATION, VEHICLES, ARTS-DESIGN, BEAUTY, FOOD, TRAVEL, SHOPPING, HOME, OUTDOORS, FASHION]. Here is the article :"
            f"{article_text}"
        )
        response = model.generate_content(prompt)

        # Parse the response into a list of topics
        topics = response.text.strip().split(" ")
        topics = [topic.strip() for topic in topics if topic.strip()]  # Clean up the topics
        for topic in topics:
            print(topic)
        cleaned_topic = []
        for topic in topics:
            if topic in VALID_TOPIC:
                cleaned_topic.append(topic)
        return cleaned_topic
    except Exception as e:
        print(f"Error extracting topics with Gemini: {e}")
        return []  # Return an empty list if there's an error
def recommend_news():
    """
    Recommend news based on user preferences.
    - Split the user_preferences dictionary into topics and their frequencies.
    - Normalize the frequencies to calculate liked_factor (between 0 and 1).
    - Pass each topic and its liked_factor to get_news.
    - Combine and return the results.
    """
    if not user_preferences:
        print("No preferences recorded yet. Showing top headlines instead.")
        return fetch_top_headlines()
    
    # Calculate the total frequency of all topics
    total_frequency = sum(user_preferences.values())
    
    # Normalize frequencies to calculate liked_factor (between 0 and 1)
    topics_with_liked_factor = [
        (topic, freq / total_frequency)  # liked_factor = freq / total_frequency
        for topic, freq in user_preferences.items()
    ]
    
    # Fetch news for each topic and combine the results
    recommended_articles = []
    for topic, liked_factor in topics_with_liked_factor:
        try:
            # Fetch news for the topic with the given liked_factor
            articles = get_news(topic, liked_factor)
            recommended_articles.extend(articles)
        except Exception as e:
            print(f"Error fetching news for topic '{topic}': {e}")
    
    # Remove duplicates (if any)
    unique_articles = list({article['url']: article for article in recommended_articles}.values())
    
    return unique_articles



def main():
    while True:
        print("\n1. Top Headlines\n2. Recommended News\n3. Exit")
        choice = input("Choose an option (1/2/3): ")
        
        if choice == "1":
            headlines = fetch_top_headlines()
            display_headlines(headlines)
            
            # Let user choose a headline
            try:
                selected_index = int(input("Enter the number of the headline you want to read: ")) - 1
                if 0 <= selected_index < len(headlines):
                    selected_headline = headlines[selected_index]
                    print(f"\nYou selected: {selected_headline['title']}")
                    
                    # Scrape and summarize the article
                    article_url = selected_headline['url']
                    print("\nScraping article...")
                    article_text = scrape_article(article_url)
                    if article_text:
                         # Extract topics using Gemini
                        topics = get_topic(article_text)
                        print("Extracted Topics:", topics)
                        # Add extracted topics to user preferences
                        for topic in topics:
                            user_preferences[topic] += 1
                        print("Topics added to your preferences.")
                        summary = summarize_with_gemini(article_text)
                        topics = get_topic(article_text)
                        print("\nSummary:\n", summary)
                    else:
                        print("Unable to scrape article content.")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")
        
        elif choice == "2":
            headlines = recommend_news()
            display_headlines(headlines)
            try:
                selected_index = int(input("Enter the number of the headline you want to read: ")) - 1
                if 0 <= selected_index < len(headlines):
                    selected_headline = headlines[selected_index]
                    print(f"\nYou selected: {selected_headline['title']}")
                    
                    # Scrape and summarize the article
                    article_url = selected_headline['url']
                    print("\nScraping article...")
                    article_text = scrape_article(article_url)
                    if article_text:
                         # Extract topics using Gemini
                        topics = get_topic(article_text)
                        print("Extracted Topics:", topics)
                        # Add extracted topics to user preferences
                        for topic in topics:
                            user_preferences[topic] += 1
                        print("Topics added to your preferences.")
                        summary = summarize_with_gemini(article_text)
                        topics = get_topic(article_text)
                        print("\nSummary:\n", summary)
                    else:
                        print("Unable to scrape article content.")
                else:
                    print("Invalid selection.")
            except ValueError:
                print("Please enter a valid number.")
        elif choice == "3":
            print("Exiting...")
            break
        
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
