"""Simple script to test the Steam scraper."""
import asyncio
from src.scraper.factory import ScraperFactory


async def test_scraper():
    """Test the Steam scraper."""
    print("Testing Steam scraper...")
    print("-" * 50)

    # Create scraper
    async with ScraperFactory.create("steam") as scraper:
        # Test search
        print("\n1. Testing search for 'Cyberpunk 2077'...")
        results = await scraper.search_game("Cyberpunk 2077")

        if results:
            print(f"Found {len(results)} results:")
            for i, game in enumerate(results[:3], 1):
                print(f"\n{i}. {game['title']}")
                print(f"   Price: ${game.get('current_price', 'N/A')}")
                print(f"   On Sale: {game.get('is_on_sale', False)}")
                print(f"   URL: {game['url'][:60]}...")

            # Test get details
            if results:
                print(f"\n2. Testing get details for first result...")
                details = await scraper.get_game_details(results[0]['url'])

                if details:
                    print(f"\nTitle: {details['title']}")
                    print(f"Current Price: ${details.get('current_price', 'N/A')}")
                    print(f"Original Price: ${details.get('original_price', 'N/A')}")
                    print(f"Discount: {details.get('discount_percentage', 0)}%")
                    print(f"On Sale: {details.get('is_on_sale', False)}")
                else:
                    print("Could not fetch game details")
        else:
            print("No results found")

    print("\n" + "-" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_scraper())
