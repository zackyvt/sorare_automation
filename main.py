THRESHOLD = -20

ALL_OFFERS_FILE = "./data/all_offers.txt"
RARE_OFFERS_FILE = "./data/rare_offers.txt"
THRESHOLD_OFFERS_FILE = "./data/threshold_offers.txt"

import requests

def dump_offers_to_file(file_path, offers):
    f = open(file_path, "a")
    for offer in offers:
        f.write(offer.log())
        f.write("\n")
    f.close()

class Offer:
    def __init__(self, data):
        self.id = data["id"]
        self.blockchain_id = data["blockchainId"]
        self.price = int(data["price"]) / (10 ** 18)
        self.card = data["card"]["slug"]
        self.rarity = data["card"]["rarity"]
        self.average_price = None
        self.price_change = None
    
    def set_average_price(self, average_price):
        self.average_price = average_price
        self.price_change = ((self.price - average_price) / average_price) * 100

    def log(self):
        log = ""
        log += "-- " + self.card + " --" + "\n"
        log += "id: " + self.id + "\n"
        log += "blockchain_id: " + self.blockchain_id + "\n"
        log += "rarity: " + self.rarity + "\n"
        log += "price: ETH " + str(self.price) + "\n"
        log += "historical price: ETH " + ('N/A' if self.average_price is None else str(self.average_price)) + "\n"
        log += "price change: " + ('N/A' if self.price_change is None else (str(self.price_change) + "%")) + "\n"
        return log

def main():
    end_cursor = None
    while True:
        end_cursor, offers = get_offers(end_cursor)
        rare_offers = []
        threshold_offers = []
        for offer in offers:
            if(offer.rarity == "rare"):
                offer.set_average_price(get_average_price(offer.blockchain_id))
                rare_offers.append(offer)
                if offer.price_change <= THRESHOLD:
                    threshold_offers.append(offer)
        dump_offers_to_file(ALL_OFFERS_FILE, offers)
        dump_offers_to_file(RARE_OFFERS_FILE, rare_offers)
        dump_offers_to_file(THRESHOLD_OFFERS_FILE, threshold_offers)
        if(end_cursor == None):
            break

def get_offers(end_cursor=None):
    endpoint = "https://api.sorare.com/graphql"
    query = """
        {{
            transferMarket {{
                singleSaleOffers{after} {{
                    nodes {{
                        id
                        blockchainId
                        price
                        card {{
                            slug
                            rarity
                        }}
                    }}
                    pageInfo {{
                        endCursor
                        hasNextPage
                    }}
                }}
            }}
        }}
    """
    query = query.format(after = (("(after: \"" + end_cursor + "\")") if end_cursor is not None else ""))
    r = requests.post(endpoint, json={"query": query})
    offers = []
    for offer_data in r.json()["data"]["transferMarket"]["singleSaleOffers"]["nodes"]:
        offers.append(Offer(offer_data))
    return (
        r.json()["data"]["transferMarket"]["singleSaleOffers"]["pageInfo"]["endCursor"] if r.json()["data"]["transferMarket"]["singleSaleOffers"]["pageInfo"]["hasNextPage"] else None, 
        offers
    )

def get_average_price(blockchain_id):
    h = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
        }
    r = requests.get("https://www.soraredata.com/api/offers/details/" + blockchain_id, headers=h)
    return r.json()["sent_cards_value"]

if __name__ == "__main__":
    main()