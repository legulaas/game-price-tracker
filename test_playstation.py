"""Simple script to test the PlayStation Store scraper."""
import asyncio
from src.scraper.factory import ScraperFactory


async def test_playstation_scraper():
    """Test the PlayStation Store scraper."""
    print("Testing PlayStation Store scraper...")
    print("-" * 50)

    # Create scraper
    async with ScraperFactory.create("playstation") as scraper:
        # Test search
        print("\n1. Testing search for 'God of War'...")
        results = await scraper.search_game("God of War")

        if results:
            print(f"Found {len(results)} results:")
            for i, game in enumerate(results[:3], 1):
                print(f"\n{i}. {game['title']}")
                print(f"   Price: R$ {game.get('current_price', 'N/A')}")
                print(f"   On Sale: {game.get('is_on_sale', False)}")
                if game.get('discount_percentage'):
                    print(f"   Discount: {game['discount_percentage']}%")
                print(f"   URL: {game['url'][:80]}...")

            # Test get details (optional - can be slow)
            # if results and input("\nFetch details for first result? (y/n): ").lower() == 'y':
            #     print(f"\n2. Testing get details for first result...")
            #     details = await scraper.get_game_details(results[0]['url'])
            #
            #     if details:
            #         print(f"\nTitle: {details['title']}")
            #         print(f"Current Price: R$ {details.get('current_price', 'N/A')}")
            #         print(f"Original Price: R$ {details.get('original_price', 'N/A')}")
            #         print(f"Discount: {details.get('discount_percentage', 0)}%")
            #         print(f"On Sale: {details.get('is_on_sale', False)}")
        else:
            print("No results found")

    print("\n" + "-" * 50)
    print("Test completed!")


if __name__ == "__main__":
    asyncio.run(test_playstation_scraper())
