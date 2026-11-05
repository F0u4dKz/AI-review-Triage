"""Review text templates per issue category and sentiment.

Placeholders: {product}, {carrier}, {days_late} (already includes the unit, e.g. "1 day", "3 days").
"""

ISSUE_CATEGORIES = ["delivery", "quality", "price", "support", "payment", "other"]
SENTIMENTS = ["positive", "neutral", "negative"]

RATING_RANGE = {
    "positive": (4, 5),
    "neutral": (3, 3),
    "negative": (1, 2),
}

TEMPLATES: dict[str, dict[str, list[str]]] = {
    "delivery": {
        "positive": [
            "My {product} arrived a day early with {carrier}, really impressed by the shipping speed.",
            "Fast delivery, the {product} was well packed and the {carrier} driver was friendly.",
            "Ordered on Monday, got the {product} on Wednesday. Smooth delivery, thank you!",
        ],
        "neutral": [
            "The {product} arrived on time, nothing special to say about the delivery.",
            "Delivery with {carrier} was ok, the tracking updates were a bit slow though.",
        ],
        "negative": [
            "The {product} arrived {days_late} late and {carrier} never answered my calls.",
            "Still waiting... the {product} showed up {days_late} after the promised date. Unacceptable.",
            "Package was left outside in the rain by {carrier}, the box of my {product} was soaked.",
            "{days_late} of delay for a simple {product}. I will think twice before ordering again.",
        ],
    },
    "quality": {
        "positive": [
            "The {product} feels premium and works perfectly, great build quality.",
            "Very happy with the {product}, solid materials and it does exactly what it promises.",
        ],
        "neutral": [
            "The {product} does the job, but the finish feels a bit cheap for the price.",
            "Decent {product}. Not amazing, not bad either.",
        ],
        "negative": [
            "The {product} broke after two weeks of normal use. Very poor quality.",
            "My {product} stopped working after three days, clearly a defective unit.",
            "The {product} looks nothing like the photos, the material is thin and scratched easily.",
        ],
    },
    "price": {
        "positive": [
            "Great value for money, the {product} is cheaper than in stores and just as good.",
            "Got the {product} on sale, excellent deal for this quality.",
        ],
        "neutral": [
            "The {product} is fine but a little overpriced compared to similar products.",
        ],
        "negative": [
            "Way too expensive for what the {product} is. I found the same thing for half the price elsewhere.",
            "The price of the {product} went up right after I ordered, feels like a scam.",
        ],
    },
    "support": {
        "positive": [
            "I had a question about my {product} and customer service answered within an hour. Excellent support.",
            "Support team was super helpful when I needed to change my order for the {product}.",
        ],
        "neutral": [
            "Contacted support about the {product}, got an answer after two days. It was fine.",
        ],
        "negative": [
            "I emailed customer service three times about my {product} and nobody ever replied.",
            "Support was rude and refused to help with my broken {product}. Worst service ever.",
            "Chat support kept sending me copy-paste answers about the {product}, never solved my issue.",
        ],
    },
    "payment": {
        "positive": [
            "Checkout for the {product} was quick and payment went through without any issue.",
        ],
        "neutral": [
            "Payment for the {product} worked on the second try, a bit annoying but ok.",
        ],
        "negative": [
            "I was charged twice for my {product} and I am still waiting for the refund.",
            "My card payment failed for the {product} but the money was taken anyway. I want a refund now.",
            "Refund for my returned {product} still not received after three weeks.",
        ],
    },
    "other": {
        "positive": [
            "Love the {product}, will definitely order again from this shop.",
            "Everything was perfect, the {product} makes a great gift.",
        ],
        "neutral": [
            "Bought the {product} for my brother, he says it is ok.",
            "The {product} is as described.",
        ],
        "negative": [
            "The website is confusing and I ordered the wrong {product} because of it.",
            "Not satisfied overall with the {product}, it is not what I expected.",
        ],
    },
}

PII_SUFFIXES = [
    " You can reach me at {email}.",
    " Call me back on {phone} please.",
    " My email is {email} if you need more details.",
    " Contact me at {phone} or {email}.",
]
